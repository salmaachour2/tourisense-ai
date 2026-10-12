import { Injectable } from '@angular/core';
import { HeroStat, ModuleItem, SpaceItem } from '../models/site-content.model';

@Injectable({
  providedIn: 'root'
})
export class SiteContentService {
  getHeroStats(): HeroStat[] {
    return [
      { label: 'Modules IA', value: '04' },
      { label: 'Espaces', value: '02' },
      { label: 'Semaines', value: '08' }
    ];
  }

  getModules(): ModuleItem[] {
    return [
      {
        title: 'Prévision des flux',
        description: 'Estime les arrivées et les mouvements touristiques avec une granularité régionale.',
        tags: ['LSTM', 'Prophet']
      },
      {
        title: 'Détection des tendances',
        description: 'Repère les thèmes émergents et les nouvelles destinations en vogue.',
        tags: ['NLP', 'Transformer']
      },
      {
        title: 'Alertes précoces',
        description: 'Active des notifications avant les pics ou les ruptures de flux.',
        tags: ['XGBoost', 'Isolation Forest']
      },
      {
        title: 'Cartographie intelligente',
        description: 'Superpose les données et les insights pour guider les décisions terrain.',
        tags: ['GeoJSON', 'K-Means']
      }
    ];
  }

  getSpaces(): SpaceItem[] {
    return [
      {
        title: 'Grand public',
        description: 'Une expérience conversationnelle qui recommande une destination selon les préférences exprimées en texte libre.',
        features: ['Recommandation naturelle', 'Choix personnalisé', 'Expérience mobile-first'],
        route: '/public',
        accent: 'sand'
      },
      {
        title: 'Institutionnel',
        description: 'Un dashboard analytique dédié aux flux, tendances, alertes précoces et cartographie des destinations.',
        features: ['Prévision des flux', 'Tendances en temps réel', 'Alertes de gestion'],
        route: '/institutionnel',
        accent: 'teal'
      }
    ];
  }
}
