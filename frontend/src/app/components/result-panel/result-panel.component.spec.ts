import { TestBed, ComponentFixture } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { ResultPanelComponent } from './result-panel.component';

describe('ResultPanelComponent', () => {
  let fixture: ComponentFixture<ResultPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResultPanelComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(ResultPanelComponent);
  });

  it('renders the empty state by default', () => {
    fixture.detectChanges();
    const el = fixture.nativeElement.querySelector('[data-testid="empty"]');
    expect(el?.textContent).toContain('Submit to see a prediction');
  });

  it('renders skeleton placeholders in the loading state', () => {
    fixture.componentRef.setInput('state', 'loading');
    fixture.detectChanges();
    const skeleton = fixture.nativeElement.querySelector('[data-testid="loading"]');
    expect(skeleton).not.toBeNull();
  });

  it('renders prediction, probability, latency, and model version on success', () => {
    fixture.componentRef.setInput('state', 'success');
    fixture.componentRef.setInput('result', {
      prediction: 1,
      probability: 0.876,
      latency_ms: 42,
      model_version: '7',
    });
    fixture.detectChanges();

    const el = fixture.nativeElement;
    expect(el.querySelector('[data-testid="prediction"]')?.textContent).toContain('1');
    expect(el.querySelector('[data-testid="probability"]')?.textContent).toContain('0.876');
    expect(el.querySelector('[data-testid="latency"]')?.textContent).toContain('42 ms');
    expect(el.querySelector('[data-testid="model-version"]')?.textContent).toContain('v7');
  });

  it('renders the error message and exposes a Retry button on error', () =>
    new Promise<void>((resolve) => {
      fixture.componentRef.setInput('state', 'error');
      fixture.componentRef.setInput('error', {
        kind: 'server',
        message: 'Inference unavailable',
        status: 500,
      });
      fixture.detectChanges();

      const el = fixture.nativeElement.querySelector('[data-testid="error"]');
      expect(el?.textContent).toContain('Inference unavailable');
      expect(el?.textContent).toContain('500');

      const retry: HTMLButtonElement = fixture.nativeElement.querySelector(
        '[data-testid="retry"]',
      );
      let emitted = false;
      fixture.componentInstance.retry.subscribe(() => (emitted = true));
      retry.click();
      expect(emitted).toBe(true);
      resolve();
    }));
});
