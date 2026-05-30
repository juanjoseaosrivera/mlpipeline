import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import type {
  PredictPayload,
  PredictResponse,
  PredictionError,
} from '../models/prediction.model';

@Injectable({ providedIn: 'root' })
export class MlService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiBaseUrl}/api/predict`;

  getPrediction(payload: PredictPayload): Observable<PredictResponse> {
    return this.http
      .post<PredictResponse>(this.endpoint, payload)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => this.mapError(err))));
  }

  private mapError(err: HttpErrorResponse): PredictionError {
    if (err.status === 0) {
      return { kind: 'network', message: 'Inference unavailable' };
    }
    if (err.status === 422) {
      return { kind: 'validation', message: 'Invalid payload' };
    }
    if (err.status >= 500) {
      return { kind: 'server', message: 'Inference unavailable', status: err.status };
    }
    return { kind: 'unknown', message: 'Request failed', status: err.status };
  }
}
