# Accessibility Permissions Setup

## The Issue

The application was failing with a cryptic `AXIsProcessTrusted` error because:

1. **Wrong Import Method**: The code was trying to use `Quartz.AXIsProcessTrusted()` which isn't available in the pyobjc-framework-Quartz module with the standard import method.

2. **Missing Permissions**: macOS accessibility permissions hadn't been granted to allow the app to control Notion.

## The Fix

### Code Changes

1. **Updated `src/ax/client.py`**:
   - Now uses `ctypes` to load ApplicationServices framework functions directly
   - Added better error messages with clear instructions
   - Added static methods `is_trusted()` and `request_permissions()` for permission checks

2. **Added New Diagnostic Command**:
   - New CLI command: `check-permissions`
   - Shows permission status and Python executable path
   - Attempts to trigger the system permissions dialog
   - Provides step-by-step instructions

### How to Grant Permissions

Run the diagnostic tool:
```bash
python -m src.cli check-permissions
```

This will:
- Check if permissions are granted
- Show you which Python executable needs permissions
- Trigger a system dialog to grant permissions
- Provide clear instructions

Alternatively, manually grant permissions:

1. Open **System Settings** (or System Preferences)
2. Go to **Privacy & Security** → **Accessibility**
3. Click the lock icon 🔒 and authenticate
4. Look for one of these in the list:
   - Your Terminal app (Terminal, iTerm2, Warp, etc.)
   - Python (`/Users/thierry/Documents/code/actioner-test/venv/bin/python`)
5. Check the box ☑️ to enable it
6. If not in the list, click **"+"** and add it manually
7. **IMPORTANT**: Completely restart your terminal application after granting permissions

### Verify Permissions

After granting permissions and restarting your terminal:

```bash
# Check permissions
python -m src.cli check-permissions

# Try extraction
python -m src.cli extract "Topinambourgs au vinaigre"
```

## Technical Details

### Why ctypes?

The pyobjc framework uses lazy loading for some Apple framework functions. The `AXIsProcessTrusted()` and related functions from ApplicationServices weren't being loaded properly through the standard `import Quartz` mechanism.

Using `ctypes` to load the framework directly ensures:
- Reliable access to the AX functions
- Proper return type handling
- Better error handling

### The Functions

```python
# Load ApplicationServices framework
_appservices = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')

# Configure function signatures
_AXIsProcessTrusted = _appservices.AXIsProcessTrusted
_AXIsProcessTrusted.restype = ctypes.c_bool
_AXIsProcessTrusted.argtypes = []
```

## Next Steps

Once permissions are granted, you can:

1. **Extract a single page**:
   ```bash
   python -m src.cli extract "Page Name"
   ```

2. **List all pages**:
   ```bash
   python -m src.cli list-pages
   ```

3. **Extract all pages**:
   ```bash
   python -m src.cli extract-all
   ```

4. **Validate against API**:
   ```bash
   export NOTION_TOKEN="your_token_here"
   python -m src.cli validate "Page Name"
   ```

## Troubleshooting

### Still getting permission errors?

1. Make sure you've **completely restarted** your terminal (quit and reopen, don't just open a new tab)
2. Check that the **exact Python executable** is listed in Accessibility preferences
3. Try adding **both** your terminal app AND the Python executable
4. On some macOS versions, you may need to **remove and re-add** the permission

### Permission dialog doesn't appear?

If running `check-permissions` doesn't show a dialog:
- The permission may already be in System Settings (check manually)
- You might need to run with elevated privileges
- Try manually adding the Python executable through System Settings

### Error: "Command not found"

Make sure your virtual environment is activated:
```bash
source venv/bin/activate
```

