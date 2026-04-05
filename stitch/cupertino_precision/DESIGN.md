# Design System Document

## 1. Overview & Creative North Star: "The Editorial Canvas"

This design system is built upon the concept of **The Editorial Canvas**. It moves beyond functional utility into the realm of high-end digital publishing. By leveraging the 2024 Apple aesthetic, we treat every interface as a curated exhibition of information. 

The "template" look is avoided through **Surgical Whitespace** and **Intentional Asymmetry**. We do not use lines to define structure; we use the absence of elements and the weight of typography to guide the eye. This system is designed to feel quiet yet authoritative, using a high-contrast hierarchy to make content feel like a premium physical artifact.

---

## 2. Colors & Tonal Depth

Our palette is rooted in a monochromatic base, punctuated by a singular, vibrant accent. It relies on the physics of light rather than the rigidity of lines.

### The Palette
- **Primary:** `primary` (#0059B5) / `primary_container` (#0071E3) - Used for critical actions and brand presence.
- **Surface:** `surface` (#FAF8FE) / `surface_container_lowest` (#FFFFFF) - The foundation of the "Canvas."
- **Text:** `on_surface` (#1A1B1F) for primary impact; `on_secondary_container` (#636264) for metadata.

### The "No-Line" Rule
Sectioning must never be achieved via 1px solid borders. Boundaries are defined through:
1. **Background Color Shifts:** A `surface_container_low` section sitting directly on a `surface` background.
2. **Negative Space:** Utilizing the 96px vertical padding (`xl` spacing) to signal a change in context.

### The "Glass & Gradient" Rule
To add "soul" to the digital interface, primary CTAs should utilize a subtle linear gradient from `primary` to `primary_container`. For floating navigation or modals, employ **Glassmorphism**:
- **Background:** `rgba(255, 255, 255, 0.7)` (Surface color at 70%).
- **Effect:** `backdrop-filter: blur(20px)`.
- This creates an integrated, high-end feel where the background colors bleed through the UI layers.

---

## 3. Typography: The Narrative Hierarchy

We utilize **SF Pro** (with Inter as a secondary fallback) to create an editorial rhythm. The typography is the primary "decoration" of the system.

*   **Display (Large/Medium):** `display-lg` (3.5rem) / `display-md` (2.75rem). Set with tight letter-spacing (-0.02em). This is for "Hero" moments where the words are the visual.
*   **Headlines:** `headline-lg` (2rem). Used to introduce major content sections. Must have significant bottom margin (24px) to breathe.
*   **Body:** `body-lg` (1rem). The workhorse. Always prioritize line-height (1.5) for readability.
*   **Labels:** `label-md` (0.75rem). Used for micro-copy and eyebrow headlines. Often rendered in uppercase with slight letter-spacing (+0.05em) for a "Technical Chic" look.

---

## 4. Elevation & Depth: Tonal Layering

Traditional shadows are replaced by **Tonal Layering**. We treat the UI as stacked sheets of fine paper.

*   **The Layering Principle:** Depth is achieved by "stacking" tiers. Place a `surface_container_lowest` (#FFFFFF) card on a `surface_container_low` (#F4F3F8) section. The delta in brightness creates a natural, soft lift.
*   **Ambient Shadows:** For floating elements (e.g., a "Save" FAB), use an extra-diffused shadow: `box-shadow: 0 10px 40px rgba(29, 29, 31, 0.06)`. Note the color is a tinted version of `on_surface`, not pure black.
*   **The Ghost Border:** If accessibility requires a container edge, use a "Ghost Border": `outline-variant` (#C1C6D6) at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons
*   **Primary:** Pill-shaped (`rounded-full`), `primary_container` background, white text. Transitions: `0.2s ease`. Hover: 10% darken.
*   **Secondary:** Pill-shaped, `surface_container_high` background, `primary` text. No border.
*   **Tertiary:** Text-only with an icon suffix. Uses `primary` text.

### Cards
*   **Structure:** 12px corner radius (`DEFAULT`).
*   **Visuals:** No dividers. Separate internal content groups with 24px of whitespace. Use `surface_container_lowest` for the card body against a `surface_container` background.

### Input Fields
*   **Style:** Minimalist. A subtle `surface_container_high` background with a bottom-only "Ghost Border" that transforms into a `primary` 2px border on focus.
*   **Success/Error:** Use `tertiary` (#006A26) for success and `error` (#BA1A1A) for validation, but keep the icons minimal (20px).

### Selection Chips
*   **Interaction:** Use `surface_container_highest` for unselected and `on_surface` (dark) for selected states to create high-contrast "Inky" toggles.

---

## 6. Do's and Don'ts

### Do
*   **Do** center all primary content within the 980px max-width container to maintain a focused, "Apple-style" reading experience.
*   **Do** use asymmetrical layouts (e.g., a headline on the left, body text on the right) to create visual interest.
*   **Do** prioritize `96px` vertical padding between major sections to let the brand "breathe."

### Don't
*   **Don't** use 1px solid dividers (e.g., `<hr>`). Use whitespace or a 4px height background-color shift.
*   **Don't** use standard "Drop Shadows." If an element doesn't feel elevated through color alone, use the Ambient Shadow spec.
*   **Don't** use "Alert Red" for warnings; use the `warning` (#FF9F0A) token to maintain the sophisticated palette.