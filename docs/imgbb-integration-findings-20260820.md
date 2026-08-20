# ImgBB integration findings — 2026-08-20

## Official source

- API documentation: https://api.imgbb.com/

## Verified API behavior

- ImgBB API v1 accepts POST or GET; POST is preferred for uploads.
- Uploads may be binary multipart data, base64 data, or an image URL.
- The documented maximum image size is up to 32 MB.
- The API key is required.
- An optional expiration value can automatically delete an upload after 60–15,552,000 seconds.
- The response is JSON and includes a `success` status plus uploaded-image information.

## Baak Books implementation decision

- The browser will send the selected image to a Baak Books Pages Function instead of embedding the ImgBB API key in `runtime-config.js` or the public HTML.
- The Pages Function will read `IMGBB_API_KEY` from Cloudflare Pages secret variables and forward the multipart upload to `https://api.imgbb.com/1/upload`.
- The admin UI will validate image type and size before upload, reject unsafe SVG files, compress large raster images when possible, and show clear errors.
- Firestore will store only image metadata and the returned ImgBB URLs in `imageLibrary`; removing an image from the library will not claim to delete it from ImgBB.

## Reference-only Afak Carpet behavior

- Reference repository was read only; no files were changed there.
- Its media-library behavior stores reusable image links, supports a picker modal, and explicitly distinguishes removing an item from the library from deleting the remote ImgBB image.
- Reference source examined locally: `/tmp/afak-carpet-reference/admin.html` and `/tmp/afak-carpet-reference/app.js`.

## Security and test implications

- Never commit the provided ImgBB key to GitHub, runtime-config.js, or the browser bundle.
- Test missing/invalid secret, unauthenticated access, non-admin access, oversized files, invalid MIME types, unsafe SVG, ImgBB 4xx/5xx, timeout, malformed JSON, duplicate metadata, and retry behavior.
- The public website should read only approved image URLs or public settings; it must not expose the upload endpoint to anonymous users.

## User-provided key

A key was supplied in chat for configuration. It is intentionally not copied into this document or any repository file. It should be entered as a Cloudflare Pages secret named `IMGBB_API_KEY` and, for local testing only, in `.dev.vars` (which must remain ignored).

> Note: because the key was shared in chat, rotate it in ImgBB if it has ever been exposed publicly or committed elsewhere.

## Status

This document is research and design input only. Implementation and deployment remain pending local validation and user approval.

## Checksum/source note

This file preserves the official API URL and the verified constraints needed for implementation; no credentials are stored here.
