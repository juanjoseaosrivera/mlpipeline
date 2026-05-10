import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="border-b border-neutral-800 px-6 py-4 flex items-center gap-4">
      <h1 class="text-base font-semibold tracking-tight">Intelligent Detection Platform</h1>
      <span class="text-xs font-mono text-neutral-400">v2.0.0</span>
    </header>
    <main class="px-6 py-8">
      <router-outlet />
    </main>
  `,
})
export class AppComponent {}
