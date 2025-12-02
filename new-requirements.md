# New Requirements Guide

## Overview

This guide walks you through upgrading your MCP demo stack to add professional document generation capabilities (Word, Excel, PDF). You'll add 4 new services and make minimal changes to your existing setup.

**Time Required:** 2-3 hours  
**Skill Level:** Follow the steps in order

---

## What's Changing

### ✅ **Services You're Keeping** (No Changes)
- `mailhog` - Email testing UI
- `time-mcp` - Time/timezone tools
- `filesystem-mcp` - File operations
- `memory-mcp` - Persistent memory
- `email-mcp` - Email with attachments
- `mcpo` - OpenAPI proxy (gets updated config)

### ➕ **Services You're Adding** (New)
1. `excel-mcp` - Create Excel workbooks with charts
2. `word-mcp` - Create Word documents
3. `pdf-mcp` - Generate PDFs from HTML
4. `analytics-mcp` - Data analysis and charts

### ❌ **Services You're Removing**
- None! We're only adding capabilities.

---

## Step-by-Step Implementation

### Step 1: Update Your Project Structure

Add these new directories to your project:

```bash
cd /path/to/your/mcp-project

# Create new service directories
mkdir -p excel-mcp/excel_mcp
mkdir -p word-mcp/word_mcp
mkdir -p pdf-mcp/pdf_mcp
mkdir -p analytics-mcp/analytics_mcp
```

Your project should now look like this:

```
mcp-project/
├── docs/                    # Shared workspace (existing)
├── email-mcp/              # Existing
├── time-bridge/            # Existing
├── filesystem-bridge/      # Existing
├── memory-bridge/          # Existing
├── excel-mcp/              # NEW
├── word-mcp/               # NEW
├── pdf-mcp/                # NEW
├── analytics-mcp/          # NEW
├── mcpo-config.json        # Update this
├── docker-compose.yml      # Update this
└── .env                    # Update this
```

---

### Step 2: Create Excel MCP Service

**What it does:** Creates Excel workbooks with formatting and charts.

#### Create `excel-mcp/excel_mcp/server.py`:

```python
import logging
import os
from pathlib import Path
from typing import List, Optional
from fastmcp import FastMCP
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("excel-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

mcp = FastMCP("excel")

@mcp.tool
async def create_excel_workbook(
    sheets: List[dict],
    output_filename: str,
    add_charts: bool = True
) -> dict:
    """
    Create an Excel workbook with multiple sheets.
    
    Args:
        sheets: List of sheets with structure:
            [{
                "name": "Sheet1",
                "data": {
                    "columns": ["Region", "Revenue", "Orders"],
                    "rows": [
                        {"Region": "East", "Revenue": 50000, "Orders": 120},
                        {"Region": "West", "Revenue": 75000, "Orders": 180}
                    ]
                },
                "chart": {
                    "type": "bar",
                    "title": "Revenue by Region"
                }
            }]
        output_filename: Name of output file
        add_charts: Whether to add charts
    """
    wb = Workbook()
    wb.remove(wb.active)
    
    for sheet_def in sheets:
        ws = wb.create_sheet(title=sheet_def["name"])
        data = sheet_def["data"]
        
        # Write headers
        for col_idx, col_name in enumerate(data["columns"], 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Write data rows
        for row_idx, row_data in enumerate(data["rows"], 2):
            for col_idx, col_name in enumerate(data["columns"], 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data.get(col_name))
        
        # Auto-adjust column widths
        for col in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max_length + 2
        
        # Add chart if requested
        if add_charts and "chart" in sheet_def:
            chart = BarChart() if sheet_def["chart"].get("type") == "bar" else LineChart()
            chart.title = sheet_def["chart"].get("title", "Chart")
            
            data_ref = Reference(ws, min_col=2, min_row=1, max_row=len(data["rows"]) + 1)
            cats = Reference(ws, min_col=1, min_row=2, max_row=len(data["rows"]) + 1)
            
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats)
            ws.add_chart(chart, "E5")
    
    output_path = WORKSPACE / output_filename
    wb.save(output_path)
    
    logger.info(f"Created Excel workbook: {output_path}")
    
    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "absolute_path": str(output_path),
        "size": output_path.stat().st_size,
        "sheets": len(sheets)
    }

if __name__ == "__main__":
    mcp.run()
```

#### Create `excel-mcp/requirements.txt`:

```txt
fastmcp>=2.13.2
openpyxl>=3.1.2
```

#### Create `excel-mcp/Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY excel_mcp ./excel_mcp
COPY start-excel.sh /usr/local/bin/start-excel.sh
RUN chmod +x /usr/local/bin/start-excel.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-excel.sh"]
```

#### Create `excel-mcp/start-excel.sh`:

```bash
#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m excel_mcp.server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
```

---

### Step 3: Create Word MCP Service

**What it does:** Creates professional Word documents with tables and formatting.

#### Create `word-mcp/word_mcp/server.py`:

```python
import logging
import os
from pathlib import Path
from typing import List, Optional
from fastmcp import FastMCP
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("word-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

mcp = FastMCP("word")

@mcp.tool
async def create_word_report(
    title: str,
    sections: List[dict],
    output_filename: str,
    subtitle: Optional[str] = None
) -> dict:
    """
    Create a professional Word document.
    
    Args:
        title: Report title
        sections: List of sections with structure:
            [{
                "heading": "Executive Summary",
                "level": 1,
                "content": "This week's performance shows...",
                "table": {
                    "columns": ["Region", "Revenue"],
                    "rows": [{"Region": "East", "Revenue": "50K"}]
                },
                "bullet_points": ["Point 1", "Point 2"]
            }]
        output_filename: Name of output file
        subtitle: Optional subtitle (e.g., "Week Ending Dec 1, 2024")
    """
    doc = Document()
    
    # Title
    title_para = doc.add_heading(title, 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    if subtitle:
        subtitle_para = doc.add_paragraph(subtitle)
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_para.runs[0].font.size = Pt(14)
        subtitle_para.runs[0].font.color.rgb = RGBColor(128, 128, 128)
    
    doc.add_page_break()
    
    # Sections
    for section in sections:
        level = section.get("level", 1)
        doc.add_heading(section["heading"], level)
        
        if "content" in section:
            doc.add_paragraph(section["content"])
        
        if "bullet_points" in section:
            for point in section["bullet_points"]:
                doc.add_paragraph(point, style='List Bullet')
        
        if "table" in section:
            table_data = section["table"]
            table = doc.add_table(
                rows=len(table_data["rows"]) + 1,
                cols=len(table_data["columns"])
            )
            table.style = 'Light Grid Accent 1'
            
            # Headers
            hdr_cells = table.rows[0].cells
            for i, col in enumerate(table_data["columns"]):
                hdr_cells[i].text = col
                hdr_cells[i].paragraphs[0].runs[0].font.bold = True
            
            # Data rows
            for row_idx, row in enumerate(table_data["rows"], 1):
                row_cells = table.rows[row_idx].cells
                for col_idx, col_name in enumerate(table_data["columns"]):
                    row_cells[col_idx].text = str(row.get(col_name, ""))
    
    output_path = WORKSPACE / output_filename
    doc.save(output_path)
    
    logger.info(f"Created Word document: {output_path}")
    
    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "absolute_path": str(output_path),
        "size": output_path.stat().st_size,
        "sections": len(sections)
    }

if __name__ == "__main__":
    mcp.run()
```

#### Create `word-mcp/requirements.txt`:

```txt
fastmcp>=2.13.2
python-docx>=1.1.0
```

#### Create `word-mcp/Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY word_mcp ./word_mcp
COPY start-word.sh /usr/local/bin/start-word.sh
RUN chmod +x /usr/local/bin/start-word.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-word.sh"]
```

#### Create `word-mcp/start-word.sh`:

```bash
#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m word_mcp.server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
```

---

### Step 4: Create PDF MCP Service

**What it does:** Converts HTML to professional PDFs.

#### Create `pdf-mcp/pdf_mcp/server.py`:

```python
import logging
import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from weasyprint import HTML, CSS

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("pdf-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

mcp = FastMCP("pdf")

@mcp.tool
async def create_pdf_from_html(
    html_content: str,
    output_filename: str,
    css: Optional[str] = None
) -> dict:
    """
    Create a PDF from HTML content.
    
    Args:
        html_content: HTML content or path to HTML file (relative to workspace)
        output_filename: Name of output PDF file
        css: Optional CSS stylesheet content for styling
    """
    output_path = WORKSPACE / output_filename
    
    # Check if html_content is a file path
    html_file = WORKSPACE / html_content
    if html_file.exists() and html_file.is_file():
        html = HTML(filename=str(html_file))
    else:
        html = HTML(string=html_content)
    
    stylesheets = []
    if css:
        stylesheets.append(CSS(string=css))
    
    html.write_pdf(output_path, stylesheets=stylesheets)
    
    logger.info(f"Created PDF: {output_path}")
    
    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "absolute_path": str(output_path),
        "size": output_path.stat().st_size
    }

if __name__ == "__main__":
    mcp.run()
```

#### Create `pdf-mcp/requirements.txt`:

```txt
fastmcp>=2.13.2
weasyprint>=60.0
```

#### Create `pdf-mcp/Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates nodejs npm \
       libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
       libffi-dev shared-mime-info \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pdf_mcp ./pdf_mcp
COPY start-pdf.sh /usr/local/bin/start-pdf.sh
RUN chmod +x /usr/local/bin/start-pdf.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-pdf.sh"]
```

#### Create `pdf-mcp/start-pdf.sh`:

```bash
#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m pdf_mcp.server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
```

---

### Step 5: Create Analytics MCP Service

**What it does:** Merges data, calculates metrics, generates charts.

#### Create `analytics-mcp/analytics_mcp/server.py`:

```python
import logging
import os
from pathlib import Path
from typing import List, Optional
from fastmcp import FastMCP
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("analytics-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

mcp = FastMCP("analytics")

@mcp.tool
async def merge_excel_files(
    file_paths: List[str],
    output_filename: str
) -> dict:
    """
    Merge multiple Excel files into a single dataset.
    
    Args:
        file_paths: List of Excel file paths (relative to workspace)
        output_filename: Output filename for merged data (CSV or Excel)
    """
    dfs = []
    for fp in file_paths:
        full_path = WORKSPACE / fp
        df = pd.read_excel(full_path)
        dfs.append(df)
    
    merged = pd.concat(dfs, ignore_index=True)
    
    output_path = WORKSPACE / output_filename
    if output_filename.endswith('.csv'):
        merged.to_csv(output_path, index=False)
    else:
        merged.to_excel(output_path, index=False)
    
    logger.info(f"Merged {len(file_paths)} files into {output_path}")
    
    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "rows": len(merged),
        "columns": list(merged.columns)
    }

@mcp.tool
async def calculate_summary_stats(
    file_path: str,
    group_by: Optional[str] = None
) -> dict:
    """
    Calculate summary statistics from data.
    
    Args:
        file_path: Path to data file (CSV or Excel)
        group_by: Optional column to group by (e.g., "Region")
    """
    full_path = WORKSPACE / file_path
    
    if file_path.endswith('.csv'):
        df = pd.read_csv(full_path)
    else:
        df = pd.read_excel(full_path)
    
    if group_by and group_by in df.columns:
        summary = df.groupby(group_by).agg({
            col: ['sum', 'mean', 'count'] 
            for col in df.select_dtypes(include='number').columns
        }).to_dict()
    else:
        summary = df.describe().to_dict()
    
    logger.info(f"Calculated stats for {file_path}")
    
    return {
        "summary": summary,
        "total_rows": len(df)
    }

@mcp.tool
async def generate_chart(
    file_path: str,
    chart_type: str,
    x_column: str,
    y_column: str,
    output_filename: str,
    title: Optional[str] = None
) -> dict:
    """
    Generate a chart from data.
    
    Args:
        file_path: Path to data file
        chart_type: Type of chart ('bar', 'line', 'pie')
        x_column: Column for x-axis
        y_column: Column for y-axis
        output_filename: Output image filename (PNG)
        title: Optional chart title
    """
    full_path = WORKSPACE / file_path
    
    if file_path.endswith('.csv'):
        df = pd.read_csv(full_path)
    else:
        df = pd.read_excel(full_path)
    
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'bar':
        plt.bar(df[x_column], df[y_column])
    elif chart_type == 'line':
        plt.plot(df[x_column], df[y_column], marker='o')
    elif chart_type == 'pie':
        plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
    
    if title:
        plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.tight_layout()
    
    output_path = WORKSPACE / output_filename
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Generated {chart_type} chart: {output_path}")
    
    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "size": output_path.stat().st_size,
        "chart_type": chart_type
    }

if __name__ == "__main__":
    mcp.run()
```

#### Create `analytics-mcp/requirements.txt`:

```txt
fastmcp>=2.13.2
pandas>=2.0.0
matplotlib>=3.8.0
openpyxl>=3.1.0
```

#### Create `analytics-mcp/Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analytics_mcp ./analytics_mcp
COPY start-analytics.sh /usr/local/bin/start-analytics.sh
RUN chmod +x /usr/local/bin/start-analytics.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-analytics.sh"]
```

#### Create `analytics-mcp/start-analytics.sh`:

```bash
#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m analytics_mcp.server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
```

---

### Step 6: Update Docker Compose

Replace your `docker-compose.yml` with this updated version:

```yaml
version: "3.9"

networks:
  mcp-net:
    driver: bridge

volumes:
  memory-data:

services:
  # ========================================
  # EXISTING SERVICES (No Changes)
  # ========================================
  
  mailhog:
    image: mailhog/mailhog:latest
    container_name: mailhog
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${MAILHOG_WEB_PORT:-2005}:8025"
      - "${MAILHOG_SMTP_PORT:-2025}:1025"

  time-mcp:
    build:
      context: ./time-bridge
    container_name: time-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${TIME_MCP_PORT:-2001}:8000"

  filesystem-mcp:
    build:
      context: ./filesystem-bridge
    container_name: filesystem-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${FILESYSTEM_MCP_PORT:-2002}:8000"
    environment:
      FILESYSTEM_ROOT: ${FILESYSTEM_ROOT:-/docs}
      FS_BASE_DIRECTORY: ${FILESYSTEM_ROOT:-/docs}
    volumes:
      - ./docs:${FILESYSTEM_ROOT:-/docs}:rw

  memory-mcp:
    build:
      context: ./memory-bridge
    container_name: memory-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${MEMORY_MCP_PORT:-2003}:8000"
    environment:
      MEMORY_FILE_PATH: /data/memory.json
    volumes:
      - memory-data:/data

  email-mcp:
    build:
      context: ./email-mcp
    container_name: email-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${EMAIL_MCP_PORT:-2004}:8000"
    environment:
      SMTP_HOST: ${SMTP_HOST:-mailhog}
      SMTP_PORT: ${SMTP_PORT:-1025}
      SMTP_FROM_DEFAULT: ${SMTP_FROM_DEFAULT:-noreply@example.test}
      ATTACH_ROOT: ${ATTACH_ROOT:-/attachments}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - ./docs:${ATTACH_ROOT:-/attachments}:ro

  mcpo:
    image: ghcr.io/open-webui/mcpo:main
    container_name: mcpo
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${MCPO_PORT:-2010}:8000"
    command: ["--config", "/app/config.json", "--port", "8000"]
    volumes:
      - ./mcpo-config.json:/app/config.json:ro

  # ========================================
  # NEW SERVICES (Document Generation)
  # ========================================

  excel-mcp:
    build:
      context: ./excel-mcp
    container_name: excel-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${EXCEL_MCP_PORT:-2006}:8000"
    environment:
      WORKSPACE: /workspace
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - ./docs:/workspace:rw

  word-mcp:
    build:
      context: ./word-mcp
    container_name: word-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${WORD_MCP_PORT:-2007}:8000"
    environment:
      WORKSPACE: /workspace
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - ./docs:/workspace:rw

  pdf-mcp:
    build:
      context: ./pdf-mcp
    container_name: pdf-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${PDF_MCP_PORT:-2008}:8000"
    environment:
      WORKSPACE: /workspace
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - ./docs:/workspace:rw

  analytics-mcp:
    build:
      context: ./analytics-mcp
    container_name: analytics-mcp
    restart: unless-stopped
    networks:
      - mcp-net
    ports:
      - "${ANALYTICS_MCP_PORT:-2009}:8000"
    environment:
      WORKSPACE: /workspace
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - ./docs:/workspace:rw
```

---

### Step 7: Update MCPO Configuration

Replace your `mcpo-config.json` with this updated version:

```json
{
  "mcpServers": {
    "time": {
      "type": "streamable-http",
      "url": "http://time-mcp:8000/mcp"
    },
    "filesystem": {
      "type": "streamable-http",
      "url": "http://filesystem-mcp:8000/mcp"
    },
    "memory": {
      "type": "streamable-http",
      "url": "http://memory-mcp:8000/mcp"
    },
    "email": {
      "type": "streamable-http",
      "url": "http://email-mcp:8000/mcp"
    },
    "excel": {
      "type": "streamable-http",
      "url": "http://excel-mcp:8000/mcp"
    },
    "word": {
      "type": "streamable-http",
      "url": "http://word-mcp:8000/mcp"
    },
    "pdf": {
      "type": "streamable-http",
      "url": "http://pdf-mcp:8000/mcp"
    },
    "analytics": {
      "type": "streamable-http",
      "url": "http://analytics-mcp:8000/mcp"
    }
  }
}
```

---

### Step 8: Update Environment Variables

Add these new ports to your `.env` file:

```bash
# Existing ports (keep these)
TIME_MCP_PORT=2001
FILESYSTEM_MCP_PORT=2002
MEMORY_MCP_PORT=2003
EMAIL_MCP_PORT=2004
MAILHOG_WEB_PORT=2005
MAILHOG_SMTP_PORT=2025
MCPO_PORT=2010

# NEW: Document generation ports
EXCEL_MCP_PORT=2006
WORD_MCP_PORT=2007
PDF_MCP_PORT=2008
ANALYTICS_MCP_PORT=2009

# Existing settings (keep these)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM_DEFAULT=noreply@example.test
ATTACH_ROOT=/attachments
LOG_LEVEL=INFO
LOCAL_TIMEZONE=America/New_York
FILESYSTEM_ROOT=/docs
```

---

### Step 9: Build and Start Services

Now run these commands to start everything:

```bash
# Stop existing services
make down

# Build new services (this will take 5-10 minutes first time)
docker compose build

# Start all services
make up

# Check that all services are running
make ps

# Watch logs to verify startup
make logs
```

You should see all services starting:

```
✓ mailhog         Running
✓ time-mcp        Running
✓ filesystem-mcp  Running
✓ memory-mcp      Running
✓ email-mcp       Running
✓ excel-mcp       Running (NEW)
✓ word-mcp        Running (NEW)
✓ pdf-mcp         Running (NEW)
✓ analytics-mcp   Running (NEW)
✓ mcpo            Running
```

---

### Step 10: Verify Services Are Working

Run these health checks:

```bash
# Check all health endpoints
curl http://localhost:2001/healthz  # time
curl http://localhost:2002/healthz  # filesystem
curl http://localhost:2003/healthz  # memory
curl http://localhost:2004/healthz  # email
curl http://localhost:2006/healthz  # excel (NEW)
curl http://localhost:2007/healthz  # word (NEW)
curl http://localhost:2008/healthz  # pdf (NEW)
curl http://localhost:2009/healthz  # analytics (NEW)

# Each should return: {"status":"ok"}
```

Check MCPO is exposing all tools:

```bash
# Visit these URLs in your browser:
http://localhost:2010/excel/docs
http://localhost:2010/word/docs
http://localhost:2010/pdf/docs
http://localhost:2010/analytics/docs
```

---

### Step 11: Configure Open WebUI

Now connect Open WebUI to your new tools.

**Option A: Via MCPO (Recommended - Single Configuration)**

1. Open Open WebUI
2. Go to **Settings → Admin → External Tools**
3. Click **Add Tool Server**
4. Configure:
   - **Type:** `MCP Streamable HTTP`
   - **URL:** `http://mcpo:8000/mcp` (or `http://host.docker.internal:2010/mcp` if on host)
   - **Name:** `All MCP Tools`
5. Click **Test Connection**
6. You should see all 9 tools listed

**Option B: Individual Tool Servers (More Control)**

Add each tool separately:

| Name | URL |
|------|-----|
| time | `http://time-mcp:8000/mcp` |
| filesystem | `http://filesystem-mcp:8000/mcp` |
| memory | `http://memory-mcp:8000/mcp` |
| email | `http://email-mcp:8000/mcp` |
| excel | `http://excel-mcp:8000/mcp` |
| word | `http://word-mcp:8000/mcp` |
| pdf | `http://pdf-mcp:8000/mcp` |
| analytics | `http://analytics-mcp:8000/mcp` |

---

### Step 12: Test the Complete Workflow

Create a test prompt in Open WebUI:

```
I have 3 Excel files in the docs folder: 
- region_east.xlsx
- region_west.xlsx  
- region_central.xlsx

Please:
1. Merge these files into a single dataset
2. Calculate total revenue by region
3. Create a bar chart showing revenue comparison
4. Create a Word document summarizing the findings
5. Create an Excel workbook with the merged data and a chart
6. Create a PDF version of the Word document
7. Email all files to ops@example.com with subject "Regional Analysis"
```

The agent should orchestrate all 4 new tools plus email to complete this workflow.

Check MailHog at `http://localhost:2005` to see the email with all attachments.

---

## What Changed in Your Project

### Architecture Before:
```
Open WebUI
    ↓
MCPO Proxy
    ↓
[time, filesystem, memory, email] ← 4 tools
```

### Architecture After:
```
Open WebUI
    ↓
MCPO Proxy
    ↓
[time, filesystem, memory, email, excel, word, pdf, analytics] ← 8 tools
```

### New Capabilities:
1. **Excel Generation** - Create workbooks with charts
2. **Word Documents** - Professional reports with tables
3. **PDF Creation** - High-quality PDFs from HTML
4. **Data Analytics** - Merge data, calculate stats, create charts

### All Services Use:
- ✅ FastMCP 2.0 for custom tools
- ✅ Supergateway for HTTP bridging
- ✅ Streamable HTTP protocol
- ✅ MCPO for Open WebUI integration
- ✅ Shared `/docs` workspace

---

## Troubleshooting

### Services won't start:
```bash
# Check logs
docker compose logs excel-mcp
docker compose logs word-mcp

# Common issue: port conflicts
# Solution: Change ports in .env
```

### Health checks fail:
```bash
# Restart specific service
docker compose restart excel-mcp

# Rebuild if needed
docker compose build excel-mcp
docker compose up -d excel-mcp
```

### Open WebUI can't connect:
```bash
# If Open WebUI is on host, use:
http://localhost:2010/mcp

# If Open WebUI is in Docker, use:
http://mcpo:8000/mcp

# Or connect directly to each service:
http://excel-mcp:8000/mcp
```

### Tools not showing in Open WebUI:
1. Test MCPO directly: `curl http://localhost:2010/excel/docs`
2. Check MCPO logs: `docker compose logs mcpo`
3. Verify mcpo-config.json is mounted: `docker compose exec mcpo cat /app/config.json`

---

## Summary

You've successfully added **4 new document generation services** to your MCP demo stack:

- ✅ Excel workbooks with charts
- ✅ Word documents with formatting
- ✅ PDF generation from HTML
- ✅ Data analytics and visualization

All services:
- Use FastMCP 2.0 (latest)
- Expose Streamable HTTP endpoints
- Integrate through MCPO
- Share the `/docs` workspace
- Are accessible from Open WebUI