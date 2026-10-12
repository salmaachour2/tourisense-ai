import { Routes } from '@angular/router';
import { BackofficePageComponent } from './backoffice/backoffice-page.component';
import { HomePageComponent } from './frontoffice/pages/home-page/home-page.component';
import { InstitutionnelPageComponent } from './frontoffice/pages/institutionnel-page/institutionnel-page.component';
import { PublicPageComponent } from './frontoffice/pages/public-page/public-page.component';

export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', component: HomePageComponent },
  { path: 'public', component: PublicPageComponent },
  { path: 'institutionnel', component: InstitutionnelPageComponent },
  { path: 'backoffice', component: BackofficePageComponent },
  { path: '**', redirectTo: 'home' }
];

