import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { MlService } from './ml.service';
import type { PredictResponse } from '../models/prediction.model';

describe('MlService', () => {
  let service: MlService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MlService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('POSTs the payload and returns a typed response', () =>
    new Promise<void>((resolve) => {
      const payload = { feature_1: 0.1, feature_2: -0.4, category: 2 };
      const body: PredictResponse = {
        prediction: 1,
        probability: 0.87,
        latency_ms: 12,
        model_version: '3',
      };

      service.getPrediction(payload).subscribe((r) => {
        expect(r).toEqual(body);
        resolve();
      });

      const req = http.expectOne((r) => r.url.endsWith('/api/predict'));
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(payload);
      req.flush(body);
    }));

  it('maps HTTP 500 to a typed server error', () =>
    new Promise<void>((resolve) => {
      service.getPrediction({ feature_1: 0, feature_2: 0, category: 0 }).subscribe({
        error: (err) => {
          expect(err.kind).toBe('server');
          expect(err.status).toBe(500);
          resolve();
        },
      });
      const req = http.expectOne((r) => r.url.endsWith('/api/predict'));
      req.flush({ detail: 'Inference Error' }, { status: 500, statusText: 'Server Error' });
    }));

  it('maps HTTP 422 to a typed validation error', () =>
    new Promise<void>((resolve) => {
      service.getPrediction({ feature_1: 0, feature_2: 0, category: 0 }).subscribe({
        error: (err) => {
          expect(err.kind).toBe('validation');
          resolve();
        },
      });
      const req = http.expectOne((r) => r.url.endsWith('/api/predict'));
      req.flush({ detail: [] }, { status: 422, statusText: 'Unprocessable Entity' });
    }));

  it('maps a network failure (status 0) to a typed network error', () =>
    new Promise<void>((resolve) => {
      service.getPrediction({ feature_1: 0, feature_2: 0, category: 0 }).subscribe({
        error: (err) => {
          expect(err.kind).toBe('network');
          resolve();
        },
      });
      const req = http.expectOne((r) => r.url.endsWith('/api/predict'));
      req.error(new ProgressEvent('error'), { status: 0, statusText: 'Network Error' });
    }));
});
