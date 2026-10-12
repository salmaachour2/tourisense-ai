import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NavbarComponent } from '../../layout/navbar/navbar.component';
import { FooterComponent } from '../../layout/footer/footer.component';
import { SiteContentService } from '../../../shared/services/site-content.service';

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink, NavbarComponent, FooterComponent],
  templateUrl: './home-page.component.html',
  styleUrls: ['./home-page.component.scss']
})
export class HomePageComponent {
  heroStats: Array<{ label: string; value: string }> = [];
  modules: Array<{ title: string; description: string; tags: string[] }> = [];
  spaces: Array<{ title: string; description: string; features: string[]; route: string; accent: 'sand' | 'teal' }> = [];

  constructor(private readonly siteContent: SiteContentService) {
    this.heroStats = this.siteContent.getHeroStats();
    this.modules = this.siteContent.getModules();
    this.spaces = this.siteContent.getSpaces();
  }
}
