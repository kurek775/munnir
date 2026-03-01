---
name: frontend
description: Angular 21 frontend with Tailwind, Transloco i18n, CDK drag-and-drop, and ECharts visualization
---

# Front-End Engineering (The Playground)

The frontend is the user's interactive playground. Munnir relies on drag-and-drop mechanics and real-time data visualization, so the architecture must be highly reactive and optimized to prevent lag.

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Framework | Angular 21 | Standalone components only — **no `NgModules`** |
| Language | TypeScript (strict) | All API responses mapped to typed interfaces |
| Styling | Tailwind CSS | Custom Munnir palette, Light/Dark mode via CSS vars |
| Interactive UI | Angular CDK `DragDropModule` | Modular widget dashboard |
| i18n | Transloco | Lazy-loaded CS/EN JSON dictionaries |
| Charts | ECharts via `ngx-echarts` | Real-time multi-line risk profile graphs |
| Testing | Vitest (`@analogjs/vitest-angular`) | `.spec.ts` co-located next to source |
| Package Manager | pnpm | `pnpm install`, `pnpm run <script>` |
| Node | 22 LTS | |

## File Locations

| Purpose | Path |
|---|---|
| App root | `munnir-ui/src/app/` |
| Core services, guards, interceptors | `munnir-ui/src/app/core/` |
| Typed API interfaces | `munnir-ui/src/app/core/models/` |
| Shared/reusable components | `munnir-ui/src/app/shared/` |
| Feature modules | `munnir-ui/src/app/features/` |
| i18n translation files | `munnir-ui/src/assets/i18n/` |
| Tailwind & theme styles | `munnir-ui/src/styles/` |
| Routes | `munnir-ui/src/app/app.routes.ts` |
| Proxy config (dev) | `munnir-ui/proxy.conf.json` |
| Tailwind config | `munnir-ui/tailwind.config.ts` |
| Environment files | `munnir-ui/src/environments/` |

## Dev Commands

```bash
cd munnir-ui
pnpm install
pnpm start          # ng serve with proxy.conf.json → localhost:4200
pnpm test           # vitest
pnpm build          # production build
```

---

## Architecture Rules

### 1. Standalone Components Only

Every component, directive, and pipe is standalone. Never create an `NgModule`.

```typescript
@Component({
  standalone: true,
  selector: 'munnir-pnl-card',
  imports: [TranslocoModule, NgxEchartsDirective],
  templateUrl: './pnl-card.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PnlCardComponent {
  chartData = input.required<PnlDataPoint[]>();
  sessionClicked = output<string>();
}
```

### 2. Signals for All Reactive State

Use `signal`, `computed`, and `effect` — never raw `BehaviorSubject` for component state. Services that hold app-wide state use a signal-based store pattern.

```typescript
// core/store/dashboard.store.ts
@Injectable({ providedIn: 'root' })
export class DashboardStore {
  // Private writeable signals
  readonly #sessions = signal<TradingSession[]>([]);
  readonly #loading = signal(false);

  // Public read-only access
  readonly sessions = this.#sessions.asReadonly();
  readonly loading = this.#loading.asReadonly();
  readonly activeSessions = computed(() =>
    this.#sessions().filter(s => s.status === 'active')
  );

  constructor(private api: ApiService) {}

  async loadSessions(): Promise<void> {
    this.#loading.set(true);
    const data = await firstValueFrom(this.api.get<TradingSession[]>('/sessions'));
    this.#sessions.set(data);
    this.#loading.set(false);
  }
}
```

### 3. Smart vs. Dumb Components

| Type | Responsibility | Example |
|---|---|---|
| **Smart** (container) | Injects stores/services, fetches data, manages state | `DashboardPageComponent` |
| **Dumb** (presentational) | Receives data via `input()`, emits via `output()`, zero DI | `PnlCardComponent`, `DragTileComponent` |

Dumb components **never** inject services. They only communicate through inputs and outputs.

### 4. Change Detection

**Always** `ChangeDetectionStrategy.OnPush` on every component. No exceptions. Combined with Signals, this ensures Angular only re-renders when data actually changes.

### 5. Lazy-Loaded Routes

Every feature is lazy-loaded. The main `app.routes.ts` should look like:

```typescript
// app.routes.ts
export const appRoutes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard-page.component')
        .then(m => m.DashboardPageComponent),
    canActivate: [authGuard],
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./features/settings/settings-page.component')
        .then(m => m.SettingsPageComponent),
    canActivate: [authGuard],
  },
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then(m => m.LoginComponent) },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: 'dashboard' },
];
```

---

## API Interaction

### Base ApiService

All HTTP calls go through a single `ApiService`. Never call `HttpClient` directly from components or stores.

```typescript
// core/services/api.service.ts
@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  get<T>(path: string, params?: HttpParams): Observable<T> {
    return this.http.get<T>(`/api${path}`, { params });
  }

  post<T>(path: string, body: unknown): Observable<T> {
    return this.http.post<T>(`/api${path}`, body);
  }

  put<T>(path: string, body: unknown): Observable<T> {
    return this.http.put<T>(`/api${path}`, body);
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`/api${path}`);
  }
}
```

The `/api` prefix is rewritten by `proxy.conf.json` in dev and by the reverse proxy in production.

### Interceptors

```typescript
// core/interceptors/auth.interceptor.ts
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthStore).token();
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
```

Register in `app.config.ts`:

```typescript
provideHttpClient(withInterceptors([authInterceptor]))
```

### Typed Interfaces

All API response shapes live in `core/models/`. One file per domain.

```typescript
// core/models/trading-session.model.ts
export interface TradingSession {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed';
  riskProfile: RiskProfile;
  pnl: number;
  createdAt: string;   // ISO 8601
}

export interface RiskProfile {
  id: string;
  label: string;
  maxDrawdown: number;
  targetReturn: number;
}
```

---

## Tailwind Theme

The Munnir palette is defined as CSS custom properties for Light/Dark mode support, mapped in `tailwind.config.ts`.

### Key Color Tokens

| Token | Usage | Light | Dark |
|---|---|---|---|
| `--color-profit` | Positive PnL, gains | `#16a34a` | `#4ade80` |
| `--color-loss` | Negative PnL, losses | `#dc2626` | `#f87171` |
| `--color-surface` | Card/widget backgrounds | `#ffffff` | `#1e1e2e` |
| `--color-surface-alt` | Alternating rows, subtle bg | `#f8fafc` | `#252538` |
| `--color-border` | Dividers, card edges | `#e2e8f0` | `#3b3b52` |
| `--color-text` | Primary text | `#0f172a` | `#e2e8f0` |
| `--color-text-muted` | Secondary/helper text | `#64748b` | `#94a3b8` |
| `--color-accent` | CTA buttons, links, active | `#6366f1` | `#818cf8` |

Usage in templates: `class="text-profit bg-surface border-border"`.

Dark mode is toggled via a `dark` class on `<html>` and Tailwind's `darkMode: 'class'` strategy.

---

## Internationalization (Transloco)

### Key Convention

Flat dot-notation keys, grouped by feature then element:

```
feature.element.property
```

### Example: `src/assets/i18n/en.json`

```json
{
  "dashboard.title": "Dashboard",
  "dashboard.session.start": "Start Session",
  "dashboard.session.pause": "Pause",
  "dashboard.pnl.label": "Profit & Loss",
  "settings.language.label": "Language",
  "settings.theme.label": "Theme",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "common.loading": "Loading…"
}
```

### Template Usage

```html
<h1>{{ 'dashboard.title' | transloco }}</h1>
<button>{{ 'dashboard.session.start' | transloco }}</button>
```

### Adding a New Key

1. Add to **both** `en.json` and `cs.json` simultaneously.
2. Use `common.*` for shared UI strings (buttons, labels, states).
3. Never hardcode visible strings — everything goes through Transloco.

---

## ECharts Pattern

Dumb chart components receive data and options via inputs. They never fetch data.

```typescript
// shared/components/pnl-chart/pnl-chart.component.ts
@Component({
  standalone: true,
  selector: 'munnir-pnl-chart',
  imports: [NgxEchartsDirective],
  template: `
    <div echarts [options]="chartOptions()" [merge]="chartOptions()" class="h-64 w-full"></div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PnlChartComponent {
  dataPoints = input.required<PnlDataPoint[]>();
  theme = input<'light' | 'dark'>('light');

  chartOptions = computed<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: this.dataPoints().map(d => d.timestamp) },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      data: this.dataPoints().map(d => d.value),
      smooth: true,
      lineStyle: { color: this.theme() === 'dark' ? '#4ade80' : '#16a34a' },
    }],
  }));
}
```

---

## CDK Drag-and-Drop Dashboard Pattern

```typescript
// features/dashboard/dashboard-page.component.ts
@Component({
  standalone: true,
  selector: 'munnir-dashboard-page',
  imports: [CdkDropListGroup, CdkDropList, CdkDrag, PnlCardComponent],
  template: `
    <div cdkDropListGroup class="grid grid-cols-3 gap-4 p-4">
      @for (widget of store.activeSessions(); track widget.id) {
        <div cdkDropList (cdkDropListDropped)="onDrop($event)">
          <div cdkDrag class="bg-surface rounded-xl border border-border shadow-sm">
            <munnir-pnl-card
              [chartData]="widget.pnlHistory"
              (sessionClicked)="openSession(widget.id)"
            />
          </div>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPageComponent {
  store = inject(DashboardStore);

  onDrop(event: CdkDragDrop<TradingSession>) {
    moveItemInArray(this.store.activeSessions(), event.previousIndex, event.currentIndex);
  }

  openSession(id: string) { /* navigate or open detail panel */ }
}
```

---

## Control Flow Syntax

Always use the built-in `@if` / `@for` / `@switch` syntax. Never use `*ngIf`, `*ngFor`, or `*ngSwitch`.

```html
@if (store.loading()) {
  <munnir-spinner />
} @else if (store.activeSessions().length === 0) {
  <p class="text-text-muted">{{ 'dashboard.empty' | transloco }}</p>
} @else {
  @for (session of store.activeSessions(); track session.id) {
    <munnir-session-card [session]="session" />
  }
}
```

---

## Testing

| What | How |
|---|---|
| Run all | `pnpm test` (Vitest) |
| Run single file | `pnpm vitest run src/app/shared/pnl-chart/pnl-chart.component.spec.ts` |
| File placement | Co-located: `foo.component.ts` → `foo.component.spec.ts` |

### Test Example

```typescript
// shared/components/pnl-chart/pnl-chart.component.spec.ts
import { render, screen } from '@testing-library/angular';
import { PnlChartComponent } from './pnl-chart.component';

describe('PnlChartComponent', () => {
  it('should render chart container', async () => {
    await render(PnlChartComponent, {
      inputs: { dataPoints: [{ timestamp: '10:00', value: 150 }] },
    });
    expect(screen.getByRole('figure')).toBeTruthy();
  });
});
```

---

## Checklist Before Generating Frontend Code

1. Component is `standalone: true` with `ChangeDetectionStrategy.OnPush`
2. State uses `signal()` / `computed()` / `effect()` — no `BehaviorSubject` in components
3. All visible strings use Transloco keys (added to both `en.json` and `cs.json`)
4. Colors use Munnir tokens (`text-profit`, `bg-surface`, etc.) — no raw hex in templates
5. API calls go through `ApiService`, response typed in `core/models/`
6. Dumb components have zero injected services — inputs and outputs only
7. Routes are lazy-loaded via `loadComponent`
8. Control flow uses `@if` / `@for` — never `*ngIf` / `*ngFor`
9. `.spec.ts` file exists next to the new component/service