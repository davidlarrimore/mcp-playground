# Using Signed Download URLs with Open WebUI

This guide shows how the signed download URL feature integrates with Open WebUI.

## How It Works

When you ask Open WebUI to create a document using any of the MCP document generation tools, the tool automatically:

1. Creates the requested document (Excel/Word/PDF via the Document MCP, or PowerPoint via Analytics)
2. Generates a secure, signed download URL
3. Returns a user-friendly message with the download link

## User Experience

### Example Conversation

**User:** "Create an Excel spreadsheet with Q4 sales data"

**Assistant:** *[Uses Document MCP tool]*

**Tool Response (shown to user):**
```
Excel workbook created successfully with 1 sheet(s).

📥 Download your file:
http://localhost:8080/download?file=%2Fworkspace%2Fq4_sales.xlsx&expires=1764814918&filename=q4_sales.xlsx&signature=abc123...

⏰ Link expires in 24 hours
```

**Assistant:** "I've created your Excel spreadsheet with Q4 sales data. You can download it using the link above. The download link will be valid for 24 hours."

### Download Methods

Users can download the file in multiple ways:

1. **Click the link** in the chat interface (if Open WebUI renders URLs as clickable links)
2. **Copy and paste** the URL into their browser
3. **Use command-line tools**:
   ```bash
   curl -O -J "http://localhost:8080/download?file=..."
   ```
4. **Download via script** (Python, JavaScript, etc.)

## Response Format

All document generation tools return:

```json
{
  "path": "report.xlsx",
  "absolute_path": "/workspace/report.xlsx",
  "size": 12345,
  "sheets": 3,
  "message": "Excel workbook created successfully with 3 sheet(s).\n\n📥 Download your file:\nhttp://localhost:8080/download?...\n\n⏰ Link expires in 24 hours",
  "download_url": "http://localhost:8080/download?file=...&signature=...",
  "download_expires_at": 1764814918,
  "download_expires_in": 86400
}
```

The `message` field is what Open WebUI displays to the user, making the download URL easily accessible.

## Supported File Types

All document generation services provide signed download URLs:

### Document MCP
```
User: "Create a sales report spreadsheet" → Returns XLSX file with download link
User: "Generate a professional business report" → Returns DOCX file with download link
User: "Convert this HTML to PDF" → Returns PDF file with download link
```

### Analytics MCP - Charts
```
User: "Create a bar chart of revenue by region"
→ Returns PNG image with download link
```

### Analytics MCP - Presentations
```
User: "Create a PowerPoint presentation for the quarterly review"
→ Returns PPTX file with download link
```

## Link Security

The download URLs are:
- **Signed** with HMAC-SHA256 to prevent tampering
- **Time-limited** (default: 24 hours, configurable)
- **Single-purpose** - each URL is for one specific file

Users don't need to authenticate to download using the signed URL, but the URL itself serves as proof of authorization.

## Configuration for Production

When deploying to production, update these environment variables:

```bash
# Use HTTPS for production
DOWNLOAD_BASE_URL=https://your-domain.com/downloads

# Change the secret key!
DOWNLOAD_URL_SECRET=your-very-secure-random-secret-here

# Optionally adjust expiration time (in seconds)
DOWNLOAD_URL_EXPIRATION=86400  # 24 hours
```

## Integration Tips

### For AI Assistants

When presenting download links to users:
1. Include context about what file was created
2. Mention the expiration time
3. Suggest next steps (e.g., "Once downloaded, you can...")

### For Front-end Developers

The `message` field contains the pre-formatted user message. You can either:
- Display it as-is (includes emojis and formatting)
- Parse the `download_url` field separately to create a custom download button
- Use both: show the message and add a prominent "Download" button

Example UI component:
```javascript
// Extract download URL from response
const downloadUrl = response.download_url;
const filename = response.path;

// Create download button
<button onClick={() => window.open(downloadUrl, '_blank')}>
  📥 Download {filename}
</button>
```

## Troubleshooting

### Link doesn't work
- **Check expiration**: Links expire after 24 hours by default
- **Check the URL**: Ensure it wasn't modified (signature would be invalid)
- **Try regenerating**: Ask the assistant to create the file again

### Link expired
Simply ask the assistant to regenerate the document:
```
User: "Can you create that report again? The link expired."
```

### Can't download (browser blocks it)
Some browsers may block downloads from `localhost`. Either:
- Whitelist the download service URL in your browser
- Use curl/wget from command line
- Configure HTTPS with a proper domain name

## Example Workflows

### Sales Report Generation
```
User: "Create a monthly sales report with charts for all regions"
