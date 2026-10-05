# Praxis login water background

Based directly on https://threeui.com/source-code/elemental-water.json, fetched
25 September 2026. The original bundle was verified in the earlier combined workspace. The component, HTML and CSS used by this dashboard are retained here. Original UTF-8 file hashes:

| Registered file | SHA-256 |
| --- | --- |
| `ElementsBackground.tsx` | `04dfbb5d8e91e71772a34b4f963e2335458c4ffdace33071fa28b731a053ba95` |
| `sources/elemental-marks.html` | `7a6871fe99fa5e1551b27b2601f2a22dd23320ea2c90b5432c9c8e071f0b1d1d` |
| `../threeui.css` | `efe4447139f1358dd8e9be68edf6fa46cbefbd1de423a4d6c439ca61d2c8eccf` |

The canonical HTML and shared CSS remain byte-for-byte originals. The source's
registered React export is `ElementsBackground`; `LoginWaterBackground.tsx`
aliases that export to `ElementsCollection` and supplies the requested Water
configuration (speed 0.58, size 0.85, particles 0.61, hue 0, saturation/brightness/
opacity 1). No npm recreation or documentation-page embedding is involved.

User-requested adaptations are isolated in `praxisWaterSource.ts`:

- Load `assets/praxis-logo.png`, the verified supplied Praxis logo, as an
  embedded image. Rasterize its alpha into the existing SDF and particle contour
  pipeline, and sample its full color through the same refracted UV coordinates.
  The original wave equation, ripple normals, lighting, glow and particles remain.
- Place the mark in the middle of the desktop background, beside the form,
  or between the introduction and mobile form.
- Receive normalized pointer events from the host and dispatch them to the
  original panel handlers. `ElementsBackground.tsx` forwards and cleans up these
  listeners. The decorative iframe cannot intercept form clicks or keyboard focus.

The original `srcDoc` / `sandbox="allow-scripts"` rendering structure, visibility
pause, resize handling, reduced-motion behavior, and detail patches are retained.
The embedded image avoids cross-origin canvas restrictions in the opaque sandbox.
The component and shared CSS load lazily from the login page. Unmounting login
destroys the iframe and removes host listeners.

Verification: `npm run build` and `node login-water-check.mjs` from `frontend/` with
the local frontend/backend running. Browser artifacts are in `frontend/artifacts/`.
The check observes actual GPU simulation impulses from cursor movement and form
clicks, checks keyboard fields, responsive layout and reduced motion, and signs in
against the real API to confirm the scene is removed on authenticated pages.

26 September: user requested an orange website theme. The Praxis adapter now replaces only Water color constants with a warm orange palette; the source HTML and logo texture remain unchanged. Ripple behavior and login-only mounting remain intact.
