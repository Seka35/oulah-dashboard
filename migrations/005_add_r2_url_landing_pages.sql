-- Migration: Add r2_url column to landing_pages
ALTER TABLE landing_pages ADD COLUMN IF NOT EXISTS r2_url TEXT;