import path from 'path';
import { config } from '../config/index.js';
import { BaseErrorCode, McpError } from '../types-global/errors.js';
import { logger } from '../utils/internal/logger.js';
import { requestContextService } from '../utils/internal/requestContext.js';
import { sanitization } from '../utils/security/sanitization.js';
/**
 * Simple in-memory state management for the MCP server session.
 * This state is cleared when the server restarts.
 */
class ServerState {
    constructor() {
        this.defaultFilesystemPath = null;
        this.fsBaseDirectory = null;
        this.fsBaseDirectory = config.fsBaseDirectory || null;
        if (this.fsBaseDirectory) {
            // Ensure fsBaseDirectory itself is sanitized and absolute for internal use
            const initContext = requestContextService.createRequestContext({ operation: 'ServerStateInit' });
            try {
                const sanitizedBase = sanitization.sanitizePath(this.fsBaseDirectory, { allowAbsolute: true, toPosix: true });
                this.fsBaseDirectory = sanitizedBase.sanitizedPath;
                // Initialize the default path to the base directory so relative paths work out of the box.
                this.defaultFilesystemPath = this.fsBaseDirectory;
                logger.info(`Filesystem operations will be restricted to base directory: ${this.fsBaseDirectory}. Default path initialized to the base directory.`, initContext);
            }
            catch (error) {
                logger.error(`Invalid FS_BASE_DIRECTORY configured: ${this.fsBaseDirectory}. It will be ignored.`, { ...initContext, error: error instanceof Error ? error.message : String(error) });
                this.fsBaseDirectory = null; // Disable if invalid
            }
        }
    }
    /**
     * Sets the default filesystem path for the current session.
     * The path is sanitized and validated.
     *
     * @param newPath - The absolute path to set as default.
     * @param context - The request context for logging.
     * @throws {McpError} If the path is invalid or not absolute.
     */
    setDefaultFilesystemPath(newPath, context) {
        logger.debug(`Attempting to set default filesystem path: ${newPath}`, context);
        try {
            // Ensure the path is absolute before storing
            if (!path.isAbsolute(newPath)) {
                throw new McpError(BaseErrorCode.VALIDATION_ERROR, 'Default path must be absolute.', { ...context, path: newPath });
            }
            // Sanitize the absolute path (mainly for normalization and basic checks)
            // We don't restrict to a rootDir here as it's a user-provided default.
            const sanitizedPathInfo = sanitization.sanitizePath(newPath, { allowAbsolute: true, toPosix: true });
            this.defaultFilesystemPath = sanitizedPathInfo.sanitizedPath;
            logger.info(`Default filesystem path set to: ${this.defaultFilesystemPath}`, context);
        }
        catch (error) {
            logger.error(`Failed to set default filesystem path: ${newPath}`, { ...context, error: error instanceof Error ? error.message : String(error) });
            // Rethrow McpError or wrap other errors
            if (error instanceof McpError) {
                throw error;
            }
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid default path provided: ${error instanceof Error ? error.message : String(error)}`, { ...context, path: newPath, originalError: error });
        }
    }
    /**
     * Gets the currently set default filesystem path.
     *
     * @returns The absolute default path or null if not set.
     */
    getDefaultFilesystemPath() {
        return this.defaultFilesystemPath;
    }
    /**
     * Clears the default filesystem path.
     * @param context - The request context for logging.
     */
    clearDefaultFilesystemPath(context) {
        logger.info('Clearing default filesystem path.', context);
        this.defaultFilesystemPath = null;
    }
    /**
     * Resolves a given path against the default path if the given path is relative.
     * If the given path is absolute, it's returned directly after sanitization.
     * If the given path is relative and no default path is set, an error is thrown.
     *
     * @param requestedPath - The path provided by the user (can be relative or absolute).
     * @param context - The request context for logging and error handling.
     * @returns The resolved, sanitized, absolute path.
     * @throws {McpError} If a relative path is given without a default path set, or if sanitization fails.
     */
    resolvePath(requestedPath, context) {
        logger.debug(`Resolving path: ${requestedPath}`, { ...context, defaultPath: this.defaultFilesystemPath, fsBaseDirectory: this.fsBaseDirectory });
        let absolutePath;
        if (path.isAbsolute(requestedPath)) {
            absolutePath = requestedPath;
            logger.debug('Provided path is absolute.', { ...context, path: absolutePath });
        }
        else {
            if (!this.defaultFilesystemPath) {
                logger.warning('Relative path provided but no default path is set.', { ...context, path: requestedPath });
                throw new McpError(BaseErrorCode.VALIDATION_ERROR, 'Relative path provided, but no default filesystem path has been set for this session. Please provide an absolute path or set a default path first.', { ...context, path: requestedPath });
            }
            // Guard against accidental double-root prefixes (e.g., "docs/file" when default is "/docs").
            const defaultPrefix = this.defaultFilesystemPath.replace(/^[\\/]+/, '');
            const normalizedRequested = requestedPath.replace(/^[\\/]+/, '');
            const strippedRequested = normalizedRequested.startsWith(`${defaultPrefix}/`)
                ? normalizedRequested.slice(defaultPrefix.length + 1)
                : normalizedRequested;
            absolutePath = path.join(this.defaultFilesystemPath, strippedRequested);
            logger.debug(`Resolved relative path against default: ${absolutePath}`, { ...context, relativePath: requestedPath, defaultPath: this.defaultFilesystemPath });
        }
        let sanitizedAbsolutePath;
        try {
            // Sanitize the path first. allowAbsolute is true as we've resolved it.
            // No rootDir is enforced by sanitizePath itself here; boundary check is next.
            const sanitizedPathInfo = sanitization.sanitizePath(absolutePath, { allowAbsolute: true, toPosix: true });
            sanitizedAbsolutePath = sanitizedPathInfo.sanitizedPath;
            logger.debug(`Sanitized resolved path: ${sanitizedAbsolutePath}`, { ...context, originalPath: absolutePath });
        }
        catch (error) {
            logger.error(`Failed to sanitize resolved path: ${absolutePath}`, { ...context, error: error instanceof Error ? error.message : String(error) });
            if (error instanceof McpError) {
                throw error; // Rethrow validation errors from sanitizePath
            }
            throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to process path: ${error instanceof Error ? error.message : String(error)}`, { ...context, path: absolutePath, originalError: error });
        }
        // Enforce FS_BASE_DIRECTORY boundary if it's set
        if (this.fsBaseDirectory) {
            // Normalize both paths for a reliable comparison
            const normalizedFsBaseDirectory = path.normalize(this.fsBaseDirectory);
            const normalizedSanitizedAbsolutePath = path.normalize(sanitizedAbsolutePath);
            // Check if the sanitized absolute path is within the base directory
            if (!normalizedSanitizedAbsolutePath.startsWith(normalizedFsBaseDirectory + path.sep) && normalizedSanitizedAbsolutePath !== normalizedFsBaseDirectory) {
                logger.error(`Path access violation: Attempted to access path "${sanitizedAbsolutePath}" which is outside the configured FS_BASE_DIRECTORY "${this.fsBaseDirectory}".`, { ...context, requestedPath, resolvedPath: sanitizedAbsolutePath, fsBaseDirectory: this.fsBaseDirectory });
                throw new McpError(BaseErrorCode.FORBIDDEN, `Access denied: The path "${requestedPath}" resolves to a location outside the allowed base directory.`, { ...context, requestedPath, resolvedPath: sanitizedAbsolutePath });
            }
            logger.debug(`Path is within FS_BASE_DIRECTORY: ${sanitizedAbsolutePath}`, context);
        }
        return sanitizedAbsolutePath;
    }
}
// Export a singleton instance
export const serverState = new ServerState();
