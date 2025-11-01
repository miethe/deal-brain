/**
 * Image Configuration Validation Tests
 *
 * Tests for the Zod validation schema used to validate product-images.json.
 * Ensures configuration errors are caught at build time with meaningful messages.
 */

import { validateImageConfig, safeValidateImageConfig } from '../validate-image-config';
import { z } from 'zod';

describe('validateImageConfig', () => {
  const validConfig = {
    version: '1.0.0',
    baseUrl: '/images',
    manufacturers: {
      hp: {
        logo: '/images/manufacturers/hp.svg',
      },
      dell: {
        logo: '/images/manufacturers/dell.svg',
        series: {
          optiplex: '/images/manufacturers/dell-optiplex.svg',
        },
        fallback: '/images/manufacturers/dell-generic.svg',
      },
    },
    formFactors: {
      'mini-pc': {
        icon: '/images/fallbacks/mini-pc-icon.svg',
      },
      desktop: {
        icon: '/images/fallbacks/desktop-icon.svg',
        generic: '/images/fallbacks/desktop-generic.svg',
      },
    },
    cpuVendors: {
      intel: '/images/fallbacks/intel-logo.svg',
      amd: '/images/fallbacks/amd-logo.svg',
      arm: '/images/fallbacks/arm.svg',
    },
    gpuVendors: {
      nvidia: '/images/fallbacks/nvidia.svg',
      amd: '/images/fallbacks/amd.svg',
      intel: '/images/fallbacks/intel.svg',
    },
    fallbacks: {
      generic: '/images/fallbacks/generic-pc.svg',
    },
  };

  describe('valid configurations', () => {
    it('should validate a complete valid configuration', () => {
      expect(() => validateImageConfig(validConfig)).not.toThrow();
      const result = validateImageConfig(validConfig);
      expect(result.version).toBe('1.0.0');
      expect(result.baseUrl).toBe('/images');
    });

    it('should accept semantic versioning formats', () => {
      const configs = [
        { ...validConfig, version: '1.0' },
        { ...validConfig, version: '1.0.0' },
        { ...validConfig, version: '2.1.3' },
      ];

      configs.forEach((config) => {
        expect(() => validateImageConfig(config)).not.toThrow();
      });
    });

    it('should accept minimal manufacturer configuration', () => {
      const minimalConfig = {
        ...validConfig,
        manufacturers: {
          hp: {
            logo: '/images/manufacturers/hp.svg',
          },
        },
      };

      expect(() => validateImageConfig(minimalConfig)).not.toThrow();
    });

    it('should accept manufacturer with series and fallback', () => {
      const configWithSeries = {
        ...validConfig,
        manufacturers: {
          hp: {
            logo: '/images/manufacturers/hp.svg',
            series: {
              elitedesk: '/images/manufacturers/hp-elitedesk.svg',
              prodesk: '/images/manufacturers/hp-prodesk.svg',
            },
            fallback: '/images/manufacturers/hp-generic.svg',
          },
        },
      };

      expect(() => validateImageConfig(configWithSeries)).not.toThrow();
    });

    it('should accept empty manufacturers, formFactors, cpuVendors, and gpuVendors', () => {
      const minimalConfig = {
        ...validConfig,
        manufacturers: {},
        formFactors: {},
        cpuVendors: {},
        gpuVendors: {},
      };

      expect(() => validateImageConfig(minimalConfig)).not.toThrow();
    });
  });

  describe('invalid configurations', () => {
    it('should reject missing required fields', () => {
      const invalidConfigs = [
        { ...validConfig, version: undefined },
        { ...validConfig, baseUrl: undefined },
        { ...validConfig, manufacturers: undefined },
        { ...validConfig, formFactors: undefined },
        { ...validConfig, cpuVendors: undefined },
        { ...validConfig, gpuVendors: undefined },
        { ...validConfig, fallbacks: undefined },
      ];

      invalidConfigs.forEach((config) => {
        expect(() => validateImageConfig(config)).toThrow(z.ZodError);
      });
    });

    it('should reject invalid version format', () => {
      const invalidVersions = [
        { ...validConfig, version: 'v1.0.0' },
        { ...validConfig, version: '1' },
        { ...validConfig, version: 'latest' },
        { ...validConfig, version: '' },
      ];

      invalidVersions.forEach((config) => {
        expect(() => validateImageConfig(config)).toThrow(z.ZodError);
      });
    });

    it('should reject baseUrl not starting with "/"', () => {
      const invalidBaseUrls = [
        { ...validConfig, baseUrl: 'images' },
        { ...validConfig, baseUrl: 'https://example.com/images' },
        { ...validConfig, baseUrl: '' },
      ];

      invalidBaseUrls.forEach((config) => {
        expect(() => validateImageConfig(config)).toThrow(z.ZodError);
      });
    });

    it('should reject empty string paths', () => {
      const invalidConfigs = [
        {
          ...validConfig,
          manufacturers: {
            hp: { logo: '' },
          },
        },
        {
          ...validConfig,
          formFactors: {
            'mini-pc': { icon: '' },
          },
        },
        {
          ...validConfig,
          cpuVendors: {
            intel: '',
          },
        },
        {
          ...validConfig,
          gpuVendors: {
            nvidia: '',
          },
        },
        {
          ...validConfig,
          fallbacks: {
            generic: '',
          },
        },
      ];

      invalidConfigs.forEach((config) => {
        expect(() => validateImageConfig(config)).toThrow(z.ZodError);
      });
    });

    it('should reject manufacturer with empty series path', () => {
      const invalidConfig = {
        ...validConfig,
        manufacturers: {
          hp: {
            logo: '/images/manufacturers/hp.svg',
            series: {
              elitedesk: '',
            },
          },
        },
      };

      expect(() => validateImageConfig(invalidConfig)).toThrow(z.ZodError);
    });

    it('should reject manufacturer with empty fallback path', () => {
      const invalidConfig = {
        ...validConfig,
        manufacturers: {
          hp: {
            logo: '/images/manufacturers/hp.svg',
            fallback: '',
          },
        },
      };

      expect(() => validateImageConfig(invalidConfig)).toThrow(z.ZodError);
    });

    it('should reject form factor with empty generic path', () => {
      const invalidConfig = {
        ...validConfig,
        formFactors: {
          desktop: {
            icon: '/images/fallbacks/desktop-icon.svg',
            generic: '',
          },
        },
      };

      expect(() => validateImageConfig(invalidConfig)).toThrow(z.ZodError);
    });
  });

  describe('safeValidateImageConfig', () => {
    it('should return success for valid configuration', () => {
      const result = safeValidateImageConfig(validConfig);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.version).toBe('1.0.0');
      }
    });

    it('should return error for invalid configuration', () => {
      const invalidConfig = { ...validConfig, version: 'invalid' };
      const result = safeValidateImageConfig(invalidConfig);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors.length).toBeGreaterThan(0);
      }
    });

    it('should provide detailed error messages', () => {
      const invalidConfig = {
        ...validConfig,
        baseUrl: 'invalid-url',
        version: 'v1.0',
      };
      const result = safeValidateImageConfig(invalidConfig);

      expect(result.success).toBe(false);
      if (!result.success) {
        const errorMessages = result.error.errors.map((e) => e.message);
        expect(errorMessages.length).toBeGreaterThan(0);
      }
    });
  });

  describe('type inference', () => {
    it('should infer correct types from validated config', () => {
      const config = validateImageConfig(validConfig);

      // TypeScript should recognize these properties
      expect(typeof config.version).toBe('string');
      expect(typeof config.baseUrl).toBe('string');
      expect(typeof config.manufacturers).toBe('object');
      expect(typeof config.formFactors).toBe('object');
      expect(typeof config.cpuVendors).toBe('object');
      expect(typeof config.gpuVendors).toBe('object');
      expect(typeof config.fallbacks).toBe('object');
      expect(typeof config.fallbacks.generic).toBe('string');
    });

    it('should handle optional fields correctly', () => {
      const config = validateImageConfig(validConfig);

      // Series and fallback are optional in manufacturer config
      if (config.manufacturers.dell) {
        expect(config.manufacturers.dell.series).toBeDefined();
        expect(config.manufacturers.dell.fallback).toBeDefined();
      }

      // Generic is optional in form factor config
      if (config.formFactors.desktop) {
        expect(config.formFactors.desktop.generic).toBeDefined();
      }
    });
  });
});
