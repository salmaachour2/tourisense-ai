import { Component } from '@angular/core';

@Component({
  selector: 'app-backoffice-page',
  standalone: true,
  template: '<section class="backoffice-shell"><h1>Backoffice</h1><p>Section d’administration à venir.</p></section>',
  styles: [':host{display:block}.backoffice-shell{min-height:100vh;padding:3rem 2rem;background:var(--sea-950);color:var(--chott-100)}']
})
export class BackofficePageComponent {}
