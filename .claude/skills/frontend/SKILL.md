---
name: frontend
description: Angular 21 frontend with Tailwind, Transloco i18n, CDK drag-and-drop, and ECharts visualization
---

# Front-End Engineering (The Playground)

The frontend is the user's interactive playground. Because Munnir relies heavily on drag-and-drop mechanics and real-time data visualization, the frontend architecture must be highly reactive and optimized to prevent lag.

* **Core Framework:** Angular 21. Strictly utilizing Standalone components (no `NgModules`), the new `@if`/`@for` control flow syntax, and Signals (`signal`, `computed`, `effect`) for fine-grained, glitch-free reactive state management.
* **Language:** TypeScript. All API responses must map to strictly typed interfaces to catch errors at compile time.
* **Styling & UI:** Tailwind CSS. We use utility classes for layout, with a custom configuration file defining the Munnir color palette (e.g., specific greens for profit, reds for loss, and tailored Light/Dark mode variables).
* **Interactive UI:** Angular CDK. The `DragDropModule` is used to create the modular widget dashboard, allowing users to move trading sessions around the screen.
* **Internationalization (i18n):** Transloco. We maintain separate JSON dictionaries for Czech (CS) and English (EN). Transloco handles lazy-loading these files so we only load the language the user needs.
* **Data Visualization:** ECharts (via `ngx-echarts`). ECharts is highly performant with large datasets, making it ideal for rendering real-time multi-line graphs that compare different AI risk profiles simultaneously.

## File Locations

| Purpose | Path |
|---------|------|
| App root | `munnir-ui/src/app/` |
| Core services & guards | `munnir-ui/src/app/core/` |
| Shared/reusable components | `munnir-ui/src/app/shared/` |
| Feature modules | `munnir-ui/src/app/features/` |
| i18n translation files | `munnir-ui/src/assets/i18n/` |
| Tailwind & theme styles | `munnir-ui/src/styles/` |
| Routes | `munnir-ui/src/app/app.routes.ts` |
| Proxy config (dev) | `munnir-ui/proxy.conf.json` |

## Testing

* **Framework:** Vitest (via `@analogjs/vitest-angular` or Angular's built-in test runner)
* **Run:** `npx vitest` or `ng test` inside the `munnir-ui/` directory
* **Convention:** Place `.spec.ts` files next to the component/service they test

## Best Practices

* **Smart vs. Dumb Components:** Keep the components that render the charts or drag-and-drop tiles "dumb" (they only receive data via inputs and emit events). Only the parent "dashboard" component should be "smart" (fetching data from the API and managing state).
* **Change Detection:** Always use `ChangeDetectionStrategy.OnPush` to ensure Angular only re-renders components when their specific input data changes. This is crucial for a smooth dashboard experience.
* **Lazy Loading:** Route modules (like the Dashboard, Settings, or Login) should be lazy-loaded so the initial application load is lightning fast.
