OFFLINE DEPLOYMENT BUNDLE

1. Pre-stage Docker images and Python dependencies on a connected build machine.
2. Export images with docker save and copy the tar files to the isolated site.
3. Copy this repository and the exported images to the site.
4. Load images with docker load.
5. Set a site-specific SECRET_KEY and database password through an environment file.
6. Run: docker compose -f deploy/docker-compose.yml up -d
7. Verify GET /api/health.
8. Keep a pre-update backup before applying any new release.
9. Follow docs/OPERATIONS.md for rollback and restore.
