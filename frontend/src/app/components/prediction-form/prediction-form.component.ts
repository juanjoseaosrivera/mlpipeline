import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
  signal,
} from '@angular/core';

import type { PredictPayload } from '../../models/prediction.model';

@Component({
  selector: 'app-prediction-form',
  standalone: true,
  templateUrl: './prediction-form.component.html',
  styleUrl: './prediction-form.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PredictionFormComponent {
  readonly pending = input(false);
  readonly submitted = output<PredictPayload>();

  readonly feature_1 = signal<number | null>(null);
  readonly feature_2 = signal<number | null>(null);
  readonly category = signal<number | null>(null);

  readonly touched = signal({ feature_1: false, feature_2: false, category: false });

  readonly errors = computed(() => {
    const f1 = this.feature_1();
    const f2 = this.feature_2();
    const cat = this.category();
    return {
      feature_1: f1 === null || Number.isNaN(f1),
      feature_2: f2 === null || Number.isNaN(f2),
      category: cat === null || Number.isNaN(cat) || cat < 0 || !Number.isInteger(cat),
    };
  });

  readonly isValid = computed(() => {
    const e = this.errors();
    return !e.feature_1 && !e.feature_2 && !e.category;
  });

  readonly canSubmit = computed(() => this.isValid() && !this.pending());

  onInput(field: 'feature_1' | 'feature_2' | 'category', value: string): void {
    const parsed = value === '' ? null : Number(value);
    if (field === 'feature_1') this.feature_1.set(parsed);
    if (field === 'feature_2') this.feature_2.set(parsed);
    if (field === 'category') this.category.set(parsed === null ? null : Math.trunc(parsed));
  }

  onBlur(field: 'feature_1' | 'feature_2' | 'category'): void {
    this.touched.update((t) => ({ ...t, [field]: true }));
  }

  submit(): void {
    if (!this.canSubmit()) return;
    this.submitted.emit({
      feature_1: this.feature_1() as number,
      feature_2: this.feature_2() as number,
      category: this.category() as number,
    });
  }
}
