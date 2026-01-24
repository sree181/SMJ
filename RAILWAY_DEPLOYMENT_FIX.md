# Railway Deployment Fix

## Issue
Railway deployment was failing with error:
```
error: undefined variable 'npm'
at /app/.nixpacks/nixpkgs-ffeebf0acf3ae8b29f8c7049cd911b9636efd7e7.nix:19:21
```

## Root Cause
The `nixpacks.toml` file was trying to specify `npm` separately, but `npm` comes bundled with `nodejs-18_x` in Nixpacks. The syntax was also incorrect.

## Fix Applied

### 1. Updated `nixpacks.toml`
- **Before**: `nixPkgs = ["nodejs-18_x", "npm"]` ❌
- **After**: `nixPkgs = ["nodejs-18_x"]` ✅

`npm` is automatically included with Node.js, so we don't need to specify it separately.

### 2. Simplified `railway.json`
- Removed explicit `buildCommand` to let Nixpacks auto-detect from `package.json`
- Updated `startCommand` to include `--single` flag for React Router support

## Alternative: Remove nixpacks.toml (Auto-Detection)

If you still encounter issues, you can **delete `nixpacks.toml`** entirely. Railway will:
1. Auto-detect Node.js from `package.json`
2. Run `npm install` automatically
3. Run `npm run build` (from package.json scripts)
4. Use the `Procfile` for the start command

## Current Configuration

### Files:
- **`nixpacks.toml`**: Specifies Node.js 18 and build steps
- **`railway.json`**: Railway-specific configuration
- **`Procfile`**: Start command with `--single` flag for React Router
- **`package.json`**: Contains build script and dependencies

### Build Process:
1. Railway detects Node.js project
2. Installs dependencies: `npm ci`
3. Builds React app: `npm run build`
4. Starts server: `npx serve -s build -l $PORT --single`

## Testing Deployment

1. **Commit changes**:
   ```bash
   git add nixpacks.toml railway.json
   git commit -m "Fix Railway deployment configuration"
   git push
   ```

2. **Railway will automatically**:
   - Detect the push
   - Start a new deployment
   - Use the updated configuration

3. **Monitor deployment** in Railway dashboard

## If Issues Persist

### Option 1: Use Dockerfile Instead
Create a `Dockerfile`:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE $PORT
CMD ["npx", "serve", "-s", "build", "-l", "$PORT", "--single"]
```

### Option 2: Delete nixpacks.toml
Let Railway auto-detect everything from `package.json` and `Procfile`.

## Environment Variables

Make sure to set in Railway dashboard:
- `REACT_APP_API_URL`: Your backend API URL (e.g., `https://your-backend.railway.app/api`)
- `PORT`: Automatically set by Railway (don't override)

## Notes

- The `--single` flag in the serve command is crucial for React Router to work correctly
- Railway automatically sets `$PORT` environment variable
- The build output goes to the `build/` directory (standard for Create React App)
