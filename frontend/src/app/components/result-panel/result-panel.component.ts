import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import type { PredictResponse, PredictionError } from '../../models/prediction.model';

export type ResultPanelState = 'empty' | 'loading' | 'success' | 'error';

@Component({
  selector: 'app-result-panel',
  standalone: true,
  templateUrl: './result-panel.component.html',
  styleUrl: './result-panel.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ResultPanelComponent {
  readonly state = input<ResultPanelState>('empty');
  readonly result = input<PredictResponse | null>(null);
  readonly error = input<PredictionError | null>(null);
  readonly retry = output<void>();

  formatProbability(p: number): string {
    return p.toPrecision(3);
  }

  onRetry(): void {
    this.retry.emit();
  }
}
