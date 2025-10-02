# Installing Frontend Dependencies

The frontend requires several additional UI dependencies that need to be installed.

## Issue

The `node_modules` directory is currently owned by root, which prevents normal installation.

## Solution

Run one of the following commands with appropriate permissions:

### Option 1: Using sudo (if available)
```bash
sudo chown -R $USER:$USER /mnt/containers/deal-brain/node_modules
pnpm install
```

### Option 2: Using Docker
```bash
make up  # Start the docker-compose stack
# The web container will install dependencies automatically
```

### Option 3: Manual cleanup and reinstall
```bash
# Remove existing node_modules (requires sudo)
sudo rm -rf /mnt/containers/deal-brain/node_modules

# Reinstall all dependencies
pnpm install
```

## Required Dependencies

The following packages have been added to `apps/web/package.json` but need to be installed:

- `@radix-ui/react-select@^2.0.0` - Dropdown/select component primitives
- `@radix-ui/react-slider@^1.1.2` - Slider component for weight configuration
- `recharts@^2.12.0` - Chart library for visualization

## Verification

After installation, verify the packages are installed:

```bash
ls node_modules/@radix-ui/react-select
ls node_modules/@radix-ui/react-slider
ls node_modules/recharts
```

## Related Files

The following UI components were created and require these dependencies:

- `apps/web/components/ui/select.tsx` - Requires @radix-ui/react-select
- `apps/web/components/ui/slider.tsx` - Requires @radix-ui/react-slider
- `apps/web/components/profiles/weight-config.tsx` - Requires recharts
- `apps/web/components/ui/alert.tsx` - Standard component, no new deps
- `apps/web/components/ui/textarea.tsx` - Standard component, no new deps
- `apps/web/components/ui/use-toast.ts` - Hook for toast notifications
