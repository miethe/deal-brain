# Adding Product Images - User Guide

This guide explains how to add manufacturer logos, form factor icons, and series images to the Deal Brain catalog without modifying code or deploying.

## Prerequisites

- Access to the repository (file manager, FTP, or Git)
- SVG or PNG image file (512x512px recommended, max 200KB)
- Basic text editing skills

## Quick Start

Adding an image is a 3-step process:
1. **Upload** the image file to the correct directory
2. **Update** the configuration file
3. **Verify** the image appears in the app

**Total time:** ~5 minutes

---

## Step 1: Prepare Your Image

### Image Requirements
- **Format:** SVG (preferred) or PNG
- **Size:** 512x512 pixels recommended
- **File Size:** Maximum 200KB
- **Background:** Transparent or white
- **Quality:** Clean, professional logo

### Naming Convention
Use lowercase with hyphens (kebab-case):
- ✅ **Good:** `minisforum.svg`, `dell-optiplex.svg`, `mini-pc.svg`
- ❌ **Bad:** `Minisforum.svg`, `Dell OptiPlex.svg`, `DELL.SVG`, `Mini PC.svg`

**Important:** File names must be lowercase with hyphens, no spaces or uppercase letters.

### Image Optimization
Before uploading, optimize your images to reduce file size:

**For SVG files:**
1. Visit [SVGOMG](https://jakearchibald.github.io/svgomg/)
2. Upload your SVG file
3. Download the optimized version
4. Use the optimized file for upload

**For PNG files:**
1. Visit [TinyPNG](https://tinypng.com/)
2. Upload your PNG file
3. Download the compressed version
4. Use the compressed file for upload

---

## Step 2: Upload Image

### Where to Upload

Choose the correct directory based on image type:

| Image Type | Directory |
|------------|-----------|
| Manufacturer logos | `/apps/web/public/images/manufacturers/` |
| CPU vendor logos | `/apps/web/public/images/cpu-vendors/` |
| GPU vendor logos | `/apps/web/public/images/gpu-vendors/` |
| Form factor icons | `/apps/web/public/images/form-factors/` |
| Fallback images | `/apps/web/public/images/fallbacks/` |

### Option A: File Manager (Easiest)

1. Navigate to `/apps/web/public/images/`
2. Open the appropriate subdirectory (see table above)
3. Upload your image file
4. Verify the file uploaded successfully

**Example: Adding Minisforum manufacturer logo**
- Navigate to: `/apps/web/public/images/manufacturers/`
- Upload: `minisforum.svg`
- Verify: File appears in directory listing

### Option B: Git (For Developers)

```bash
# Example: Adding Minisforum manufacturer logo
cd /mnt/containers/deal-brain/apps/web/public/images/manufacturers
cp ~/Downloads/minisforum.svg .
git add minisforum.svg
git commit -m "Add Minisforum manufacturer logo"
git push
```

---

## Step 3: Update Configuration

### Locate Config File
The configuration file is located at:
```
/apps/web/config/product-images.json
```

Open this file in any text editor (Notepad, VS Code, nano, etc.).

### Configuration Structure

The file has five main sections:

```json
{
  "version": "1.0.0",
  "baseUrl": "/images",
  "manufacturers": { ... },
  "formFactors": { ... },
  "cpuVendors": { ... },
  "gpuVendors": { ... },
  "fallbacks": { ... }
}
```

### Add Your Entry

Choose the section that matches your image type:

#### For Manufacturer Logo

Add a new entry in the `"manufacturers"` section:

```json
{
  "manufacturers": {
    "hpe": {
      "logo": "/images/manufacturers/hpe.svg"
    },
    "minisforum": {
      "logo": "/images/manufacturers/minisforum.svg"
    }
  }
}
```

**Key points:**
- Add a comma after the previous entry
- Use the same name as your file (without extension)
- Path must match uploaded file location exactly

#### For CPU Vendor Logo

Add a new entry in the `"cpuVendors"` section:

```json
{
  "cpuVendors": {
    "intel": "/images/cpu-vendors/intel.svg",
    "amd": "/images/cpu-vendors/amd.svg",
    "arm": "/images/cpu-vendors/arm.svg",
    "qualcomm": "/images/cpu-vendors/qualcomm.svg"
  }
}
```

#### For GPU Vendor Logo

Add a new entry in the `"gpuVendors"` section:

```json
{
  "gpuVendors": {
    "nvidia": "/images/gpu-vendors/nvidia.svg",
    "amd": "/images/gpu-vendors/amd.svg"
  }
}
```

#### For Form Factor Icon

Add a new entry in the `"formFactors"` section:

```json
{
  "formFactors": {
    "desktop": {
      "icon": "/images/form-factors/desktop.svg"
    },
    "mini-pc": {
      "icon": "/images/form-factors/mini-pc.svg"
    },
    "mini_pc": {
      "icon": "/images/form-factors/mini-pc.svg"
    },
    "laptop": {
      "icon": "/images/form-factors/laptop.svg"
    }
  }
}
```

**Note:** Form factors may have multiple key formats (hyphenated and underscored) for compatibility.

### Important JSON Formatting Rules

Follow these rules to avoid errors:

1. **Use double quotes** `"`, not single quotes `'`
2. **Add comma after previous entry** when adding new items
3. **NO comma after last entry** in a section
4. **Match file path exactly** including `/images/` prefix
5. **Use lowercase keys** with hyphens or underscores

**Example of correct formatting:**
```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg"
    },
    "hp": {
      "logo": "/images/manufacturers/hp.svg"
    }
  }
}
```

**Common mistakes:**
```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg"  ← Missing comma
    }
    "hp": {
      "logo": '/images/manufacturers/hp.svg'    ← Single quotes (wrong!)
    },                                           ← Extra comma (wrong!)
  }
}
```

---

## Step 4: Verify

After saving the configuration file:

1. **Save the file** with your changes
2. **Refresh the Deal Brain app** in your browser (press F5)
3. **Navigate to a listing** with the relevant manufacturer/vendor
4. **Check the image displays** correctly

### How to Test

**For manufacturer logos:**
1. Go to the Listings page
2. Find or create a listing with the manufacturer you added
3. Check if the logo appears in the listing card

**For CPU/GPU vendor logos:**
1. Go to any listing details page
2. Look at the CPU or GPU section
3. Verify the vendor logo displays

**For form factor icons:**
1. Go to the Listings page
2. Find a listing with the form factor you added
3. Check if the icon appears

### If Image Doesn't Appear

Try these steps:
1. **Hard refresh browser:** Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Clear browser cache** or open in incognito/private window
3. **Wait 30 seconds** for cache to clear
4. **Check troubleshooting section** below

---

## Advanced: Adding Series-Specific Images

Series-specific images display for specific product lines within a manufacturer (e.g., Dell OptiPlex has a unique image different from other Dell products).

### When to Use Series Images

Use series images when:
- A manufacturer has distinct product lines with unique branding
- You want granular control over which image displays
- A product series has its own recognizable logo

**Examples:**
- Dell OptiPlex (business desktops)
- Dell Latitude (business laptops)
- HP EliteDesk (business desktops)
- Lenovo ThinkCentre (business desktops)

### Step 1: Upload Series Image

Create a subdirectory for the manufacturer if it doesn't exist:

```
/apps/web/public/images/manufacturers/dell/
```

Upload the series image to this subdirectory:

```
/apps/web/public/images/manufacturers/dell/optiplex.svg
/apps/web/public/images/manufacturers/dell/latitude.svg
```

### Step 2: Update Configuration

Add a `"series"` section to the manufacturer entry:

```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg",
      "series": {
        "optiplex": "/images/manufacturers/dell/optiplex.svg",
        "latitude": "/images/manufacturers/dell/latitude.svg",
        "precision": "/images/manufacturers/dell/precision.svg"
      }
    }
  }
}
```

### How Series Matching Works

The system automatically detects series names from listing data:
- **Listing with series "OptiPlex"** → Shows `/images/manufacturers/dell/optiplex.svg`
- **Listing with series "Latitude"** → Shows `/images/manufacturers/dell/latitude.svg`
- **Listing with no series** → Shows `/images/manufacturers/dell.svg` (fallback)

**Important:** Series keys must match the series field in your listing data (case-insensitive, normalized to lowercase).

### Complete Example

```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg",
      "series": {
        "optiplex": "/images/manufacturers/dell/optiplex.svg",
        "latitude": "/images/manufacturers/dell/latitude.svg"
      }
    },
    "hp": {
      "logo": "/images/manufacturers/hp.svg",
      "series": {
        "elitedesk": "/images/manufacturers/hp/elitedesk.svg",
        "prodesk": "/images/manufacturers/hp/prodesk.svg"
      }
    }
  }
}
```

---

## Troubleshooting

### Image Doesn't Appear

#### Check 1: File Path

**Problem:** Path in config doesn't match uploaded file location.

**Solution:**
1. Verify file uploaded to correct directory
2. Check file name matches exactly (case-sensitive!)
3. Ensure path in config includes `/images/` prefix
4. Check file extension is correct (`.svg` not `.SVG`)

**Example:**
- File location: `/apps/web/public/images/manufacturers/minisforum.svg`
- Config path: `/images/manufacturers/minisforum.svg` ✅
- Wrong path: `/manufacturers/minisforum.svg` ❌ (missing `/images/`)
- Wrong path: `/images/manufacturers/Minisforum.svg` ❌ (wrong case)

#### Check 2: JSON Syntax Errors

**Problem:** Invalid JSON formatting breaks the configuration.

**Solution:**
1. Copy entire config file content
2. Visit [JSONLint](https://jsonlint.com/)
3. Paste content and click "Validate JSON"
4. Fix any errors shown

**Common JSON errors:**
- Missing comma between entries
- Extra comma after last entry in section
- Single quotes instead of double quotes
- Unescaped special characters
- Missing closing brace `}`

#### Check 3: File Name Format

**Problem:** File name contains spaces, uppercase, or special characters.

**Solution:**
1. Rename file to lowercase with hyphens
2. Update config to match new file name
3. Re-upload if necessary

**Examples:**
- `Mini PC.svg` → rename to `mini-pc.svg`
- `Minisforum.svg` → rename to `minisforum.svg`
- `dell_optiplex.svg` → rename to `dell-optiplex.svg` (use hyphens, not underscores)

#### Check 4: Browser Cache

**Problem:** Browser is showing old cached version.

**Solution:**
1. Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Clear browser cache completely
3. Open in incognito/private browsing window
4. Try a different browser

#### Check 5: File Size

**Problem:** File is too large (over 200KB).

**Solution:**
1. Check file size (right-click → Properties on Windows, Get Info on Mac)
2. If over 200KB, optimize using:
   - SVG: [SVGOMG](https://jakearchibald.github.io/svgomg/)
   - PNG: [TinyPNG](https://tinypng.com/)
3. Re-upload optimized file

### Image Is Blurry or Low Quality

**Problem:** PNG image is pixelated or blurry.

**Solution:**
1. **Use SVG format instead** - SVG is vector-based and scales perfectly
2. If PNG is required, ensure minimum 512x512px resolution
3. Export at 2x resolution (1024x1024px) for high-DPI displays

**Why SVG is better:**
- Scales infinitely without quality loss
- Smaller file size (typically)
- Crisper rendering at any size

### Image Has Wrong Background Color

**Problem:** Image has solid background instead of transparent.

**Solution:**
1. Edit in vector graphics software:
   - Free: [Inkscape](https://inkscape.org/) (desktop) or [Boxy SVG](https://boxy-svg.com/) (web)
   - Paid: Adobe Illustrator, Affinity Designer
2. Remove background or set to transparent
3. Export as SVG with transparent background
4. Re-upload optimized file

### Changes Not Reflected After Upload

**Problem:** Changes made but not visible in app.

**Checklist:**
1. ✅ Edited correct config file (`/apps/web/config/product-images.json`)
2. ✅ Saved file after editing
3. ✅ File uploaded to correct directory
4. ✅ Hard refreshed browser (`Ctrl+Shift+R`)
5. ✅ Waited 30-60 seconds for cache to clear
6. ✅ Checked browser console for errors (F12 → Console tab)

**Still not working?**
- Check browser console (F12) for error messages
- Verify JSON syntax at [JSONLint](https://jsonlint.com/)
- Ask engineering team for assistance

### Series Image Not Showing

**Problem:** Series-specific image doesn't display.

**Solution:**
1. Check listing has `series` field populated
2. Verify series key in config matches series value in listing (case-insensitive)
3. Ensure series image file exists at specified path
4. Check manufacturer has both `logo` and `series` entries

**Example:**
```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg",  ← Required fallback
      "series": {
        "optiplex": "/images/manufacturers/dell/optiplex.svg"
      }
    }
  }
}
```

---

## Configuration File Reference

### Full Example

This is a complete example showing all configuration options:

```json
{
  "version": "1.0.0",
  "baseUrl": "/images",
  "manufacturers": {
    "hpe": {
      "logo": "/images/manufacturers/hpe.svg"
    },
    "dell": {
      "logo": "/images/manufacturers/dell.svg",
      "series": {
        "optiplex": "/images/manufacturers/dell/optiplex.svg",
        "latitude": "/images/manufacturers/dell/latitude.svg",
        "precision": "/images/manufacturers/dell/precision.svg"
      }
    },
    "hp": {
      "logo": "/images/manufacturers/hp.svg",
      "series": {
        "elitedesk": "/images/manufacturers/hp/elitedesk.svg",
        "prodesk": "/images/manufacturers/hp/prodesk.svg"
      }
    },
    "lenovo": {
      "logo": "/images/manufacturers/lenovo.svg",
      "series": {
        "thinkcentre": "/images/manufacturers/lenovo/thinkcentre.svg",
        "thinkpad": "/images/manufacturers/lenovo/thinkpad.svg"
      }
    }
  },
  "formFactors": {
    "desktop": {
      "icon": "/images/form-factors/desktop.svg"
    },
    "mini-pc": {
      "icon": "/images/form-factors/mini-pc.svg"
    },
    "mini_pc": {
      "icon": "/images/form-factors/mini-pc.svg"
    },
    "laptop": {
      "icon": "/images/form-factors/laptop.svg"
    },
    "all-in-one": {
      "icon": "/images/form-factors/all-in-one.svg"
    }
  },
  "cpuVendors": {
    "intel": "/images/cpu-vendors/intel.svg",
    "amd": "/images/cpu-vendors/amd.svg",
    "arm": "/images/cpu-vendors/arm.svg",
    "qualcomm": "/images/cpu-vendors/qualcomm.svg"
  },
  "gpuVendors": {
    "nvidia": "/images/gpu-vendors/nvidia.svg",
    "amd": "/images/gpu-vendors/amd.svg",
    "intel": "/images/gpu-vendors/intel.svg"
  },
  "fallbacks": {
    "generic": "/images/fallbacks/generic-pc.svg"
  }
}
```

### Configuration Schema

```typescript
interface ProductImagesConfig {
  version: string;           // Config version (currently "1.0.0")
  baseUrl: string;          // Base URL for all images ("/images")

  manufacturers: {
    [key: string]: {        // Manufacturer slug (lowercase, hyphenated)
      logo: string;         // Path to manufacturer logo
      series?: {            // Optional series-specific images
        [key: string]: string;  // Series slug → image path
      };
    };
  };

  formFactors: {
    [key: string]: {        // Form factor slug
      icon: string;         // Path to form factor icon
    };
  };

  cpuVendors: {
    [key: string]: string;  // CPU vendor slug → logo path
  };

  gpuVendors: {
    [key: string]: string;  // GPU vendor slug → logo path
  };

  fallbacks: {
    generic: string;        // Generic fallback image path
  };
}
```

---

## Best Practices

### Image Quality
1. ✅ **Always use SVG when possible** for logos and icons (vector format scales perfectly)
2. ✅ **Optimize all images** before uploading (use SVGOMG or TinyPNG)
3. ✅ **Use transparent backgrounds** for logos (not white or colored)
4. ✅ **Test images at different sizes** to ensure clarity

### File Organization
1. ✅ **Follow naming conventions** strictly (lowercase, hyphens, no spaces)
2. ✅ **Keep file names simple** and descriptive
3. ✅ **Use subdirectories** for series-specific images
4. ✅ **Document custom images** (add comments in README files)

### Configuration Management
1. ✅ **Validate JSON** before committing (use JSONLint)
2. ✅ **Test in the app** before pushing changes
3. ✅ **Use descriptive commit messages** when using Git
4. ✅ **Keep config file organized** (alphabetize entries when possible)

### Workflow
1. ✅ **Prepare image first** (optimize, rename, check size)
2. ✅ **Upload to correct directory** (double-check path)
3. ✅ **Update config immediately** after upload
4. ✅ **Test before committing** (verify in app)
5. ✅ **Commit both file and config** together

### Quality Checklist

Before committing your changes, verify:

- [ ] Image file is optimized (under 200KB)
- [ ] File name is lowercase with hyphens
- [ ] File uploaded to correct directory
- [ ] Config updated with correct path
- [ ] JSON syntax is valid (checked with JSONLint)
- [ ] Image displays correctly in app
- [ ] Hard refresh tested in browser
- [ ] Works in both light and dark mode (if applicable)
- [ ] Commit message is descriptive

---

## Quick Reference: Common Tasks

### Add Manufacturer Logo
```bash
# 1. Upload file
cp minisforum.svg /apps/web/public/images/manufacturers/

# 2. Edit config (/apps/web/config/product-images.json)
"manufacturers": {
  "minisforum": {
    "logo": "/images/manufacturers/minisforum.svg"
  }
}

# 3. Verify in app
```

### Add Form Factor Icon
```bash
# 1. Upload file
cp laptop.svg /apps/web/public/images/form-factors/

# 2. Edit config
"formFactors": {
  "laptop": {
    "icon": "/images/form-factors/laptop.svg"
  }
}

# 3. Verify in app
```

### Add Series Image
```bash
# 1. Create directory and upload
mkdir -p /apps/web/public/images/manufacturers/dell/
cp optiplex.svg /apps/web/public/images/manufacturers/dell/

# 2. Edit config
"manufacturers": {
  "dell": {
    "logo": "/images/manufacturers/dell.svg",
    "series": {
      "optiplex": "/images/manufacturers/dell/optiplex.svg"
    }
  }
}

# 3. Verify in app
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the troubleshooting section** above for common problems
2. **Review README files** in each image directory for specific guidance
3. **Validate JSON syntax** at [JSONLint](https://jsonlint.com/)
4. **Check browser console** (F12) for error messages
5. **Ask the engineering team** for assistance
6. **File an issue** in the repository with:
   - What you're trying to do
   - What you've tried so far
   - Error messages (if any)
   - Screenshots (if applicable)

---

## Related Documentation

- **Technical Implementation:** `/docs/img-001-implementation-summary.md`
- **Image Directory READMEs:**
  - `/apps/web/public/images/README.md`
  - `/apps/web/public/images/manufacturers/README.md`
  - `/apps/web/public/images/cpu-vendors/README.md`
  - `/apps/web/public/images/gpu-vendors/README.md`
  - `/apps/web/public/images/form-factors/README.md`
  - `/apps/web/public/images/fallbacks/README.md`

---

**Last Updated:** 2025-11-01
**Version:** 1.0
**Status:** Complete
