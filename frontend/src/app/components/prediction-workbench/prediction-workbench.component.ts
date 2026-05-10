import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { MlService } from '../../services/ml.service';
import type {
  PredictPayload,
  PredictResponse,
  PredictionError,
} from '../../models/prediction.model';
import { PredictionFormComponent } from '../prediction-form/prediction-form.component';
import { ResultPanelComponent, ResultPanelState } from '../result-panel/result-panel.component';

@Component({
  selector: 'app-prediction-workbench',
  standalone: true,
  imports: [PredictionFormComponent, ResultPanelComponent],
  templateUrl: './prediction-workbench.component.html',
  styleUrl: './prediction-workbench.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PredictionWorkbenchComponent {
  private readonly ml = inject(MlService);

  readonly pending = signal(false);
  readonly result = signal<PredictResponse | null>(null);
  readonly error = signal<PredictionError | null>(null);
  readonly lastPayload = signal<PredictPayload | null>(null);

  readonly state = computed<ResultPanelState>(() => {
    if (this.pending()) return 'loading';
    if (this.error() !== null) return 'error';
    if (this.result() !== null) return 'success';
    return 'empty';
  });

  onSubmit(payload: PredictPayload): void {
    this.lastPayload.set(payload);
    this.pending.set(true);
    this.error.set(null);
    this.result.set(null);

    this.ml.getPrediction(payload).subscribe({
      next: (r) => {
        this.result.set(r);
        this.pending.set(false);
      },
      error: (e: PredictionError) => {
        this.error.set(e);
        this.pending.set(false);
      },
    });
  }

  onRetry(): void {
    const last = this.lastPayload();
    if (last !== null) this.onSubmit(last);
  }
}
