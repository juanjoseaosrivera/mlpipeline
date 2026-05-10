import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/prediction-workbench/prediction-workbench.component').then(
        (m) => m.PredictionWorkbenchComponent,
      ),
  },
];
