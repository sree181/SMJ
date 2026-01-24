# Fix: npm EBUSY Cache Lock Error in Railway Frontend Build

## 🚨 Problem

Frontend build is failing with:
```
npm error EBUSY: resource busy or locked, rmdir '/app/node_modules/.cache'
```

**Root Cause**: Railway's Docker build system is trying to clean up the npm cache directory, but it's locked by another process or the build cache system.

---

## ✅ Solution: Use Alternative Cache Location

### Fix 1: Update Build Command in Railway

1. **Railway Dashboard** → **"web" service** (frontend)
2. **Settings** → **Build** section
3. **Custom Build Command**: Change to:
   ```
   rm -rf node_modules/.cache || true && npm ci --cache /tmp/.npm && npm run build
   ```
4. **Save**

This:
- Removes the cache directory (with error handling)
- Uses `/tmp/.npm` for npm cache (outside the build context)
- Then runs the build

### Fix 2: Alternative - Use npm install Instead

If the above doesn't work, try:

1. **Custom Build Command**:
   ```
   rm -rf node_modules node_modules/.cache package-lock.json && npm install && npm run build
   ```
2. **Save**

This does a fresh install without using the lock file.

### Fix 3: Update nixpacks.toml (Already Done)

The `nixpacks.toml` file has been updated to:
- Remove cache before install
- Use `/tmp/.npm` for cache location

---

## 🔧 Why This Happens

Railway's Docker build system uses layer caching. When npm tries to clean up `node_modules/.cache`, it conflicts with Docker's cache mount system, causing the `EBUSY` error.

**Solution**: Use a cache location outside the build context (`/tmp/.npm`) or remove the cache before building.

---

## ✅ Expected Result

After fix, build logs should show:
```
rm -rf node_modules/.cache || true
npm ci --cache /tmp/.npm
npm run build
Creating an optimized production build...
Build completed successfully
```

**NOT:**
```
npm error EBUSY: resource busy or locked
```

---

## 📋 Quick Checklist

- [ ] Build Command updated: `rm -rf node_modules/.cache || true && npm ci --cache /tmp/.npm && npm run build`
- [ ] `nixpacks.toml` updated (already done)
- [ ] Redeploy frontend
- [ ] Build succeeds without EBUSY errors

---

**Update the build command in Railway Settings → Build section!**
