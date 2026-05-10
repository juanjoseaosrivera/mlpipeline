import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-prediction-workbench',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="grid gap-6 md:grid-cols-2 max-w-5xl">
      <div class="rounded-md border border-neutral-800 p-6">
        <h2 class="text-sm font-semibold text-neutral-300 mb-4">Prediction form</h2>
        <p class="text-sm text-neutral-500">Form lands here in Phase 4.</p>
      </div>
      <div class="rounded-md border border-neutral-800 p-6">
        <h2 class="text-sm font-semibold text-neutral-300 mb-4">Result</h2>
        <p class="text-sm text-neutral-500">Submit to see a prediction.</p>
      </div>
    </section>
  `,
})
export class PredictionWorkbenchComponent {}
