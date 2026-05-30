import { TestBed, ComponentFixture } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { PredictionFormComponent } from './prediction-form.component';
import type { PredictPayload } from '../../models/prediction.model';

describe('PredictionFormComponent', () => {
  let fixture: ComponentFixture<PredictionFormComponent>;
  let component: PredictionFormComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PredictionFormComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(PredictionFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('is invalid initially', () => {
    expect(component.isValid()).toBe(false);
    expect(component.canSubmit()).toBe(false);
  });

  it('becomes valid when all fields hold acceptable values', () => {
    component.feature_1.set(0.1);
    component.feature_2.set(-0.4);
    component.category.set(2);
    expect(component.isValid()).toBe(true);
    expect(component.canSubmit()).toBe(true);
  });

  it('flags category < 0 as invalid', () => {
    component.feature_1.set(0.1);
    component.feature_2.set(-0.4);
    component.category.set(-1);
    expect(component.errors().category).toBe(true);
    expect(component.isValid()).toBe(false);
  });

  it('emits the payload on submit when valid', () => {
    component.feature_1.set(0.1);
    component.feature_2.set(-0.4);
    component.category.set(2);

    let emitted: PredictPayload | undefined;
    component.submitted.subscribe((p) => (emitted = p));
    component.submit();

    expect(emitted).toEqual({ feature_1: 0.1, feature_2: -0.4, category: 2 });
  });

  it('does not emit when invalid', () => {
    let emitted = false;
    component.submitted.subscribe(() => (emitted = true));
    component.submit();
    expect(emitted).toBe(false);
  });

  it('does not emit while pending, even when valid', () => {
    fixture.componentRef.setInput('pending', true);
    component.feature_1.set(0.1);
    component.feature_2.set(-0.4);
    component.category.set(2);
    fixture.detectChanges();

    let emitted = false;
    component.submitted.subscribe(() => (emitted = true));
    component.submit();

    expect(component.canSubmit()).toBe(false);
    expect(emitted).toBe(false);
  });

  it('disables the submit button while pending', () => {
    component.feature_1.set(0.1);
    component.feature_2.set(-0.4);
    component.category.set(2);
    fixture.componentRef.setInput('pending', true);
    fixture.detectChanges();

    const btn: HTMLButtonElement = fixture.nativeElement.querySelector(
      '[data-testid="submit"]',
    );
    expect(btn.disabled).toBe(true);
  });
});
