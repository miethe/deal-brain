import { z } from 'zod';

export const urlImportSchema = z.object({
  url: z
    .string()
    .min(1, 'Please enter a listing URL')
    .url('Please enter a valid URL starting with http:// or https://')
    .max(2048, 'URL is too long (max 2048 characters)')
    .refine(
      (url) => {
        // Ensure URL uses http or https
        return url.startsWith('http://') || url.startsWith('https://');
      },
      { message: 'URL must start with http:// or https://' }
    ),
  priority: z.enum(['high', 'normal']).optional().default('normal'),
});

export type UrlImportFormData = z.infer<typeof urlImportSchema>;
