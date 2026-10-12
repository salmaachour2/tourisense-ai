import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { catchError, map } from 'rxjs/operators';

export interface ForecastResult {
  region: string;
  period: string;
  values: Array<{ date: string; value: number }>;
}

export interface TrendResult {
  topics: Array<{ label: string; score: number }>;
}

export interface DestinationActivity {
  title: string;
  category: 'nature' | 'culture' | 'plage' | 'gastronomie' | 'aventure' | 'detente';
  duration: string;
  badge?: string;
}

export interface Recommendation {
  id: string;
  title: string;
  tagline: string;
  description: string;
  matchScore: number; // 0..100
  governorate: string;
  category: 'mer' | 'sahara' | 'culture' | 'nature' | 'bien-etre';
  bestSeason: string;
  budgetLevel: 'Économique' | 'Modéré' | 'Haut de gamme' | 'Luxe';
  estimatedCostPerDay: number; // in TND
  imageUrl: string;
  galleryUrls?: string[];
  lat: number;
  lon: number;
  tags: string[];
  highlights: string[];
  activities: DestinationActivity[];
  aiReasoning: string;
  funFact: string;
  weather: { temp: string; condition: string; icon: string };
  vibeBadge: string;
  mustEatSpecialty: string;
}

export interface WebSourceResult {
  title: string;
  url: string;
  snippet?: string;
  imageUrl?: string;
}

export interface ChatMessage {
  id: string;
  from: 'user' | 'bot' | 'system';
  text: string;
  time: string;
  avatar?: string;
  recommendations?: Recommendation[];
  suggestedFollowUps?: string[];
  webSources?: WebSourceResult[];
  enrichment?: Array<{ title?: string; website?: string; phone?: string; address?: string; imageUrl?: string; sourceUrl?: string; note?: string }>;
  isThinking?: boolean;
}

export interface UserPreferences {
  vibe?: string;
  budget?: string;
  travelers?: string;
  duration?: string;
  governorate?: string;
}

@Injectable({ providedIn: 'root' })
export class ModelIntegrationService {
  private readonly aiApiUrl = 'http://localhost:3001/api/ai_with_data';
  private readonly defaultGroqModel = 'openai/gpt-oss-20b';

  constructor(private http: HttpClient) {}
  /**
   * Base de données enrichie de destinations tunisiennes pour l'expérience explorateur
   */
  private readonly DESTINATIONS_DB: Recommendation[] = [
    {
      id: 'sidi-bou-said',
      title: 'Sidi Bou Saïd & Carthage',
      tagline: 'Perle bleue méditerranéenne & histoire antique',
      description: 'Village perché aux ruelles blanchies à la chaux et moucharabiehs bleu azur surplombant le golfe de Tunis, à deux pas des thermes d’Antonin et de la colline de Byrsa.',
      matchScore: 98,
      governorate: 'Tunis',
      category: 'culture',
      bestSeason: 'Printemps & Automne (Avril - Octobre)',
      budgetLevel: 'Modéré',
      estimatedCostPerDay: 160,
      imageUrl: 'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=900&q=80',
      galleryUrls: [
        'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=900&q=80',
        'https://images.unsplash.com/photo-1590073844006-33379778ae09?auto=format&fit=crop&w=900&q=80'
      ],
      lat: 36.8700,
      lon: 10.3417,
      tags: ['Vue panoramique', 'Café des Délices', 'Musées', 'Patrimoine UNESCO', 'Romantique'],
      highlights: [
        'Déguster un thé à la menthe aux pignons au mythique Café des Délices',
        'Visiter le site archéologique et les thermes romains d’Antonin à Carthage',
        'Flâner dans les galeries d’art et admirer les portes cloutées traditionnelles'
      ],
      activities: [
        { title: 'Balade guidée dans la colline artistique', category: 'culture', duration: '2h', badge: 'Incontournable' },
        { title: 'Dégustation de bambalouni chaud au sucre', category: 'gastronomie', duration: '30min', badge: 'Gourmand' },
        { title: 'Coucher de soleil sur le golfe de Tunis', category: 'detente', duration: '1h', badge: 'Photo Spot' }
      ],
      aiReasoning: 'L’accord parfait entre romantisme, charme méditerranéen et histoire millénaire de la civilisation carthaginoise.',
      funFact: 'En 1914, le peintre Paul Klee a visité Sidi Bou Saïd et s’est exclamé : « La couleur me possède ! » en découvrant la lumière tunisienne.',
      weather: { temp: '26°C', condition: 'Ciel azur dégagé', icon: '☀️' },
      vibeBadge: '🏛️ Trésor UNESCO & Romantique',
      mustEatSpecialty: 'Bambalouni croustillant & Thé aux pignons dorés'
    },
    {
      id: 'djerba',
      title: 'Djerba la Douce',
      tagline: 'Île des sables dorés, artisanat & street-art',
      description: 'L’île des Lotophages aux plages d’eau turquoise, menzels blanchis à la chaux, village musée de street-art Djerbahood et synagogue historique de la Ghriba.',
      matchScore: 96,
      governorate: 'Medenine',
      category: 'mer',
      bestSeason: 'Mai à Octobre (Soleil garanti)',
      budgetLevel: 'Modéré',
      estimatedCostPerDay: 190,
      imageUrl: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80',
      lat: 33.8050,
      lon: 10.8748,
      tags: ['Plages paradisiaques', 'Djerbahood', 'Sports nautiques', 'Famille', 'Détente'],
      highlights: [
        'Exploration des 250 fresques d’art urbain à ciel ouvert à Erriadh (Djerbahood)',
        'Journée farniente et kitesurf sur les lagons de Sidi Mahrez et Seguia',
        'Balade dans les souks d’épices et de poteries de Houmt Souk'
      ],
      activities: [
        { title: 'Sortie en bateau pirate vers l’île des Flamants Roses', category: 'plage', duration: 'Journée', badge: 'Famille' },
        { title: 'Circuit Street-Art Djerbahood à vélo électrique', category: 'culture', duration: '3h', badge: 'Tendance' },
        { title: 'Visite de la Ghriba et du musée de Guellala', category: 'culture', duration: '2h30' }
      ],
      aiReasoning: 'Une destination insulaire magique combinant farniente tropical, street-art mondial et douceur de vivre légendaire.',
      funFact: 'Homère décrivait Djerba dans l’Odyssée comme l’île où Ulysse et ses compagnons oublièrent leur patrie après avoir goûté au fruit du lotus.',
      weather: { temp: '29°C', condition: 'Ensoleillé et brise marine', icon: '🏝️' },
      vibeBadge: '🏖️ Île Paradis & Street Art',
      mustEatSpecialty: 'Riz djerbien aux herbes & Poissons grillés de la criée'
    },
    {
      id: 'tozeur',
      title: 'Tozeur & Oasis de Montagne',
      tagline: 'Porte du Sahara, canyons féeriques & décors Star Wars',
      description: 'Capitale du Djérid renommée pour ses briques d’argile ocre, son immense palmeraie, les cascades de Chebika, les gorges de Tamerza et le lac salé Chott el-Djérid.',
      matchScore: 94,
      governorate: 'Tozeur',
      category: 'sahara',
      bestSeason: 'Octobre à Avril (Climat doux désertique)',
      budgetLevel: 'Modéré',
      estimatedCostPerDay: 175,
      imageUrl: 'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=900&q=80',
      lat: 34.0167,
      lon: 8.1333,
      tags: ['Sahara', 'Oasis', 'Chebika', 'Star Wars Mos Espa', 'Aventure'],
      highlights: [
        'Lever de soleil magique et mirages sur le lac de sel géant Chott el-Djérid',
        'Raid en 4x4 vers les décors intacts de Mos Espa (Star Wars) à Ong Jmel',
        'Baignade dans les cascades naturelles de l’oasis de montagne de Chebika'
      ],
      activities: [
        { title: 'Safari 4x4 dans les dunes du Grand Erg', category: 'aventure', duration: '5h', badge: 'Frisson' },
        { title: 'Nuit en bivouac sous la voûte céleste étoilée', category: 'nature', duration: 'Nuitée', badge: 'Magique' },
        { title: 'Balade en calèche au cœur de la palmeraie millénaire', category: 'nature', duration: '1h30' }
      ],
      aiReasoning: 'Le summum de l’aventure saharienne, des paysages de cinéma et de la déconnexion totale en pleine nature.',
      funFact: 'Le célèbre décor de la ville de Tatooine dans Star Wars (Mos Espa) est encore parfaitement préservé dans les dunes de Tozeur !',
      weather: { temp: '24°C', condition: 'Ciel pur étoilé', icon: '🌌' },
      vibeBadge: '🏜️ Aventure Saharienne & Oasis',
      mustEatSpecialty: 'Dattes Deglet Nour royales & Berkookes du désert'
    },
    {
      id: 'hammamet',
      title: 'Hammamet & Cap Bon',
      tagline: 'Station balnéaire chic, vergers de jasmin & médina maritime',
      description: 'L’un des joyaux côtiers méditerranéens avec sa médina ceinte de remparts en bord de mer, ses centres de thalassothérapie d’élite et ses criques de sable blanc.',
      matchScore: 92,
      governorate: 'Nabeul',
      category: 'mer',
      bestSeason: 'Juin à Septembre',
      budgetLevel: 'Haut de gamme',
      estimatedCostPerDay: 220,
      imageUrl: 'https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?auto=format&fit=crop&w=900&q=80',
      lat: 36.4000,
      lon: 10.6167,
      tags: ['Thalasso', 'Plages dorées', 'Vie nocturne', 'Médina marine', 'Sports nautiques'],
      highlights: [
        'Coucher de soleil sur les remparts de la médina surplombant les barques',
        'Séances de thalassothérapie et spas marins d’exception',
        'Excursion vers les potiers d’art de Nabeul et le fort byzantin de Kélibia'
      ],
      activities: [
        { title: 'Cure thalasso et soins marins détox', category: 'detente', duration: 'Demi-journée', badge: 'Bien-être' },
        { title: 'Paddle et sports nautiques à Yasmine Hammamet', category: 'plage', duration: '2h' },
        { title: 'Soirée au Centre Culturel International (Villa Sebastian)', category: 'culture', duration: '2h' }
      ],
      aiReasoning: 'L’alliance idéale du bien-être balnéaire haut de gamme, du farniente marin et de la culture méditerranéenne.',
      funFact: 'La Villa Sebastian à Hammamet a été qualifiée par l’architecte Frank Lloyd Wright de « l’une des plus belles maisons au monde ».',
      weather: { temp: '28°C', condition: 'Ensoleillé et tempéré', icon: '☀️' },
      vibeBadge: '💆 Thalasso & Luxe Côtier',
      mustEatSpecialty: 'Ojja aux fruits de mer & Pâtisseries aux amandes de Nabeul'
    },
    {
      id: 'tabarka',
      title: 'Tabarka & Aïn Draham',
      tagline: 'Côte de corail, forêts de chênes-lièges & fraîcheur montagnarde',
      description: 'Entre falaises rocheuses monumentales (« Les Aiguilles »), récifs coralliens réputés mondialement et monts verdoyants de Kroumirie aux airs de Suisse tunisienne.',
      matchScore: 91,
      governorate: 'Jendouba',
      category: 'nature',
      bestSeason: 'Toute l’année (Fraîcheur estivale & charme hivernal)',
      budgetLevel: 'Économique',
      estimatedCostPerDay: 130,
      imageUrl: 'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=900&q=80',
      lat: 36.9500,
      lon: 8.7583,
      tags: ['Écotourisme', 'Randonnée', 'Plongée sous-marine', 'Forêt', 'Fraîcheur'],
      highlights: [
        'Admirer les majestueuses falaises rocheuses « Les Aiguilles » dressées face aux vagues',
        'Randonnée sous les chênes géants de la forêt d’Aïn Draham et parc d’El Feidja',
        'Plongée sous-marine et festival international de Jazz de Tabarka'
      ],
      activities: [
        { title: 'Baptême de plongée sur les récifs de corail rouge', category: 'nature', duration: '3h', badge: 'Unique' },
        { title: 'Trek panoramique dans les monts de Kroumirie', category: 'aventure', duration: '4h', badge: 'Écotourisme' },
        { title: 'Dégustation de miel de montagne et cuisine forestière', category: 'gastronomie', duration: '2h' }
      ],
      aiReasoning: 'Un havre de verdure et de fraîcheur préservé, idéal pour les amoureux de randonnée, de plongée et de grand air.',
      funFact: 'Le corail rouge de Tabarka est pêché depuis l’Antiquité et orne les joyaux des cours royales d’Europe et d’Orient.',
      weather: { temp: '22°C', condition: 'Air frais revigorant', icon: '🌲' },
      vibeBadge: '🌲 Poumon Vert & Côte de Corail',
      mustEatSpecialty: 'Couscous aux herbes sauvages & Miel d’eucalyptus pur'
    },
    {
      id: 'el-jem',
      title: 'El Jem & Mahdia',
      tagline: 'Colisée romain monumental & cité maritime des Fatimides',
      description: 'Le 3e plus grand amphithéâtre romain au monde, miraculeusement conservé, complété par les plages de sable blanc vierges et le cimetière marin poétique de Mahdia.',
      matchScore: 89,
      governorate: 'Mahdia',
      category: 'culture',
      bestSeason: 'Mars à Novembre',
      budgetLevel: 'Économique',
      estimatedCostPerDay: 120,
      imageUrl: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=900&q=80',
      lat: 35.3000,
      lon: 10.7069,
      tags: ['Archéologie romaine', 'UNESCO', 'Plages secrètes', 'Pêcheurs', 'Mosaïques'],
      highlights: [
        'Visite au cœur de l’amphithéâtre romain d’El Jem et de ses galeries souterraines',
        'Promenade au coucher du soleil sur le Cap Afrique face à la grande bleue',
        'Découverte de la porte monumentale fortifiée Skifa Kahla'
      ],
      activities: [
        { title: 'Visite nocturne du Colisée éclairé aux flambeaux', category: 'culture', duration: '2h30', badge: 'Spectaculaire' },
        { title: 'Baignade sur les plages sauvages de Mahdia', category: 'plage', duration: 'Demi-journée' },
        { title: 'Atelier de tissage traditionnel de pure soie', category: 'culture', duration: '1h30' }
      ],
      aiReasoning: 'Un voyage monumental au cœur de l’Empire romain et de l’authenticité maritime tunisienne.',
      funFact: 'L’amphithéâtre d’El Jem pouvait accueillir plus de 35 000 spectateurs, soit plus que la ville moderne aujourd’hui !',
      weather: { temp: '27°C', condition: 'Ensoleillé et brise marine', icon: '🏛️' },
      vibeBadge: '🏆 Géant Romain & Cité Maritime',
      mustEatSpecialty: 'Couscous au poisson de roche & Gâteaux à la pistache'
    },
    {
      id: 'douz-ksar-ghilane',
      title: 'Douz & Ksar Ghilane',
      tagline: 'Oasis thermale au cœur des dunes & méharées nomades',
      description: 'La source d’eau chaude naturelle de Ksar Ghilane au milieu du sable rouge saharien, le fort romain de Tisavar et le festival international du Sahara de Douz.',
      matchScore: 90,
      governorate: 'Kebili',
      category: 'sahara',
      bestSeason: 'Novembre à Mars',
      budgetLevel: 'Modéré',
      estimatedCostPerDay: 180,
      imageUrl: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=900&q=80',
      lat: 33.4519,
      lon: 9.0289,
      tags: ['Baignade thermale', 'Dromadaires', 'Bivouac nomade', 'Grand Sud', 'Étoiles'],
      highlights: [
        'Bain relaxant à 34°C dans la source chaude au milieu des palmiers et des dunes',
        'Méharée à dos de dromadaire au coucher de soleil sur les crêtes de sable',
        'Dormir dans une tente berbère traditionnelle sous des milliards d’étoiles'
      ],
      activities: [
        { title: 'Baignade thermale au bassin de Ksar Ghilane', category: 'detente', duration: '2h', badge: 'Insolite' },
        { title: 'Raid en quad ou buggy jusqu’au fort romain de Tisavar', category: 'aventure', duration: '3h', badge: 'Action' },
        { title: 'Soirée contes et musique nomade autour du feu', category: 'culture', duration: 'Soirée' }
      ],
      aiReasoning: 'L’expérience ultime du Sahara, associant relaxation thermale et immensité des dunes océaniques.',
      funFact: 'La source chaude de Ksar Ghilane a été découverte par hasard lors d’un forage pétrolier dans les années 1950 !',
      weather: { temp: '23°C', condition: 'Air pur du désert', icon: '♨️' },
      vibeBadge: '🐪 Source Chaude & Grand Erg',
      mustEatSpecialty: 'Pain de sable cuit sous la braise (Mella) & Thé bédouin'
    },
    {
      id: 'matmata',
      title: 'Matmata & Ksour Berbères',
      tagline: 'Maisons troglodytiques lunaires & greniers fortifiés',
      description: 'Habitations creusées sous terre dans des cratères rocheux, forteresses berbères spectaculaires (Ksour) et paysages lunaires célèbres pour Star Wars.',
      matchScore: 88,
      governorate: 'Medenine',
      category: 'culture',
      bestSeason: 'Automne, Hiver & Printemps',
      budgetLevel: 'Économique',
      estimatedCostPerDay: 140,
      imageUrl: 'https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=900&q=80',
      lat: 33.5097,
      lon: 10.1036,
      tags: ['Troglodyte', 'Patrimoine berbère', 'Star Wars', 'Village perché', 'Insolite'],
      highlights: [
        'Dormir dans une authentique maison troglodytique souterraine',
        'Visite du village berbère perché de Chenini et de la mosquée des 7 Dormants',
        'Exploration des Ksour fortifiés (Ksar Ouled Soltane, Ksar Haddada)'
      ],
      activities: [
        { title: 'Rencontre chaleureuse avec une famille troglodyte et thé au romarin', category: 'gastronomie', duration: '1h30', badge: 'Authentique' },
        { title: 'Trek géologique dans les canyons du Djebel Dahar', category: 'nature', duration: '3h' }
      ],
      aiReasoning: 'Un dépaysement total au cœur d’une architecture unique au monde et de traditions berbères ancestrales.',
      funFact: 'L’hôtel Sidi Driss à Matmata était la véritable maison d’enfance de Luke Skywalker sur la planète Tatooine dans Star Wars.',
      weather: { temp: '22°C', condition: 'Fraîcheur des grottes', icon: '🪐' },
      vibeBadge: '🪐 Village Troglodyte & Star Wars',
      mustEatSpecialty: 'Galette berbère au miel & Huile d’olive du Dahar'
    },
    {
      id: 'bizerte-cap-blanc',
      title: 'Bizerte & Cap Blanc',
      tagline: 'Vieux port pittoresque & point le plus septentrional d’Afrique',
      description: 'Port historique bordé de maisons aux façades blanches et bleues, kasbah médiévale, canal maritime animé et falaises blanches du Cap Blanc, pointe nord du continent africain.',
      matchScore: 86,
      governorate: 'Bizerte',
      category: 'mer',
      bestSeason: 'Mai à Octobre',
      budgetLevel: 'Économique',
      estimatedCostPerDay: 125,
      imageUrl: 'https://images.unsplash.com/photo-1506953823976-52e1fdc0149a?auto=format&fit=crop&w=900&q=80',
      lat: 37.2746,
      lon: 9.8739,
      tags: ['Vieux Port', 'Cap Blanc', 'Fruits de mer', 'Kasbah', 'Plages sauvages'],
      highlights: [
        'Café au coucher du soleil autour des barques de pêcheurs du Vieux Port',
        'Randonnée panoramique jusqu’au phare du Cap Blanc (Pointe Nord de l’Afrique)',
        'Baignade sur la sublime plage sauvage de Sidi Ali El Mekki'
      ],
      activities: [
        { title: 'Dégustation de poissons frais grillés au marché du port', category: 'gastronomie', duration: '2h', badge: 'Gourmand' },
        { title: 'Visite du Musée océanographique et de la Kasbah fortifiée', category: 'culture', duration: '2h' }
      ],
      aiReasoning: 'Une authenticité marine rare, des panoramas côtiers sauvages et une gastronomie de pêcheurs savoureuse.',
      funFact: 'Le Cap Blanc est le point géographique le plus au nord de tout le continent africain (37° 20′ Nord) !',
      weather: { temp: '25°C', condition: 'Brise iodée vivifiante', icon: '⚓' },
      vibeBadge: '⚓ Cap Nord d’Afrique & Vieux Port',
      mustEatSpecialty: 'Daurade royale grillée au feu de bois & Lablabi marin'
    }
  ];

  getAllDestinations(): Observable<Recommendation[]> {
    return of(this.DESTINATIONS_DB);
  }

  /**
   * Public recommendation entrypoint. Tries the external model server first,
   * falls back to the local scoring engine when unavailable.
   */
  recommendDestinations(query: string, preferences?: UserPreferences): Observable<Recommendation[]> {
    const payload = { query, governorate: preferences?.governorate, maxResults: 6 };
    const url = 'http://localhost:3000/api/recommendations';
    return this.http.post<{ results: Recommendation[] }>(url, payload).pipe(
      map(r => r.results || []),
      catchError(() => {
        // fallback to local scoring engine
        const local = this.recommendDestinationsLocal(query, preferences);
        return of(local).pipe(delay(250));
      })
    );
  }

  /**
   * Local scoring fallback (previous implementation).
   */
  private recommendDestinationsLocal(query: string, preferences?: UserPreferences): Recommendation[] {
    const q = (query || '').toLowerCase().trim();
    let scoredList = this.DESTINATIONS_DB.map((dest) => {
      let score = 50;

      if (q) {
        if ((q.includes('plage') || q.includes('mer') || q.includes('baign') || q.includes('kitesurf') || q.includes('côte')) && (dest.category === 'mer' || dest.tags.some(t => t.toLowerCase().includes('plage')))) {
          score += 38;
        }
        if ((q.includes('désert') || q.includes('desert') || q.includes('sahara') || q.includes('oasis') || q.includes('dune') || q.includes('dromadaire')) && dest.category === 'sahara') {
          score += 42;
        }
        if ((q.includes('histoire') || q.includes('monument') || q.includes('musée') || q.includes('romain') || q.includes('médina') || q.includes('unesco')) && (dest.category === 'culture' || dest.tags.some(t => t.toLowerCase().includes('patrimoine')))) {
          score += 38;
        }
        if ((q.includes('nature') || q.includes('randonnée') || q.includes('montagne') || q.includes('forêt') || q.includes('vert') || q.includes('calme') || q.includes('fraîcheur')) && (dest.category === 'nature' || dest.tags.some(t => t.toLowerCase().includes('randonnée')))) {
          score += 38;
        }
        if ((q.includes('luxe') || q.includes('spa') || q.includes('thalasso') || q.includes('détente') || q.includes('bien-être')) && (dest.tags.some(t => t.toLowerCase().includes('thalasso') || t.toLowerCase().includes('détente')) || dest.budgetLevel === 'Haut de gamme')) {
          score += 30;
        }
        if ((q.includes('famille') || q.includes('enfant')) && dest.tags.some(t => t.toLowerCase().includes('famille') || t.toLowerCase().includes('plage'))) {
          score += 25;
        }
        if ((q.includes('amoureux') || q.includes('couple') || q.includes('romantique')) && (dest.tags.some(t => t.toLowerCase().includes('romantique')) || dest.id === 'sidi-bou-said' || dest.id === 'djerba')) {
          score += 30;
        }
        if (dest.title.toLowerCase().includes(q) || dest.governorate.toLowerCase().includes(q)) {
          score += 45;
        }
        dest.tags.forEach(t => {
          if (q.includes(t.toLowerCase())) score += 15;
        });
      } else {
        score = dest.matchScore;
      }

      if (preferences?.governorate && preferences.governorate !== 'Tous') {
        if (dest.governorate.toLowerCase() === preferences.governorate.toLowerCase()) {
          score += 25;
        } else {
          score -= 60;
        }
      }

      if (preferences?.budget) {
        if (preferences.budget === 'Économique' && (dest.budgetLevel === 'Économique' || dest.budgetLevel === 'Modéré')) score += 15;
        if (preferences.budget === 'Luxe' && (dest.budgetLevel === 'Haut de gamme' || dest.budgetLevel === 'Luxe')) score += 15;
      }

      const finalScore = Math.min(99, Math.max(40, score));
      return { ...dest, matchScore: finalScore };
    });

    if (preferences?.governorate && preferences.governorate !== 'Tous') {
      scoredList = scoredList.filter(d => d.governorate.toLowerCase() === preferences.governorate?.toLowerCase());
    }

    scoredList.sort((a, b) => b.matchScore - a.matchScore);
    const topResults = scoredList.slice(0, 4);
    return topResults;
  }

  private matchDestinationDetails(input: Partial<any>): Recommendation | undefined {
   const titleValue = String(input?.['title'] || input?.['id'] || '').trim();
   if (!titleValue) return undefined;

   const normalized = titleValue.toLowerCase();
   return this.DESTINATIONS_DB.find(dest => {
     const destTitle = dest.title.toLowerCase();
     const destId = dest.id.toLowerCase();
     return destId.includes(normalized) || destTitle.includes(normalized) || normalized.includes(destId) || normalized.includes(destTitle.replace(/[^a-z]/g, ''));
   });
  }

  private hydrateRecommendation(raw: any): Recommendation {
   const found = this.matchDestinationDetails(raw || {});
   const sanitized = raw || {};

   const imageUrl = sanitized.imageUrl || sanitized.photoUrl || sanitized.image || found?.imageUrl || found?.galleryUrls?.[0] || '';
   const galleryUrls = Array.isArray(sanitized.galleryUrls) && sanitized.galleryUrls.length
     ? sanitized.galleryUrls
     : (Array.isArray(found?.galleryUrls) ? found.galleryUrls : []);

   return {
     id: sanitized.id || found?.id || (sanitized.title ? sanitized.title.replace(/\s+/g, '-').toLowerCase() : String(Math.random())),
     title: sanitized.title || found?.title || '',
     tagline: sanitized.reason || sanitized.tagline || found?.tagline || '',
     description: sanitized.description || found?.description || '',
     matchScore: Number.isFinite(Number(sanitized.score)) ? Math.round(Number(sanitized.score) * 100) : (found?.matchScore ?? 0),
     governorate: sanitized.governorate || found?.governorate || '',
     category: (sanitized.category || found?.category || 'culture') as Recommendation['category'],
     bestSeason: sanitized.bestSeason || found?.bestSeason || '',
     budgetLevel: (sanitized.budgetLevel || found?.budgetLevel || 'Modéré') as Recommendation['budgetLevel'],
     estimatedCostPerDay: Number(sanitized.estimatedCostPerDay ?? sanitized.price ?? sanitized.cost ?? found?.estimatedCostPerDay ?? 0),
     imageUrl,
     galleryUrls,
     lat: Number(sanitized.lat ?? found?.lat ?? 0),
     lon: Number(sanitized.lon ?? found?.lon ?? 0),
     tags: Array.isArray(sanitized.tags) ? sanitized.tags : (found?.tags ?? []),
     highlights: Array.isArray(sanitized.highlights) ? sanitized.highlights : (found?.highlights ?? []),
     activities: Array.isArray(sanitized.activities) ? sanitized.activities : (found?.activities ?? []),
     aiReasoning: sanitized.reason || sanitized.aiReasoning || found?.aiReasoning || '',
     funFact: sanitized.funFact || found?.funFact || '',
     weather: sanitized.weather || found?.weather || { temp: '', condition: '', icon: '' },
     vibeBadge: sanitized.vibeBadge || found?.vibeBadge || '',
     mustEatSpecialty: sanitized.mustEatSpecialty || found?.mustEatSpecialty || ''
   };
  }

  /**
   * Génère une réponse d'assistance IA chaleureuse, dynamique et personnalisée
   */
  generateBotResponse(userPrompt: string, preferences?: UserPreferences): Observable<{
    message: string;
    recommendations: Recommendation[];
    followUps: string[];
    webSources: WebSourceResult[];
    enrichment: Array<{ title?: string; website?: string; phone?: string; address?: string; imageUrl?: string; sourceUrl?: string; note?: string }>;
  }> {
    // Try the local model proxy first (model-recommendation server). If it fails, fall back to the local generator.
    const payload: any = {
      query: userPrompt,
      governorate: preferences?.governorate && preferences.governorate !== 'Tous' ? preferences.governorate : undefined,
      model: this.defaultGroqModel,
      top_k: 5
    };

    return this.http.post<any>(this.aiApiUrl, payload).pipe(
      map(resp => {
        // resp may be { data: <modelResponse>, recommendations: [...] }
        let recs: Recommendation[] = resp && resp.recommendations ? resp.recommendations : [];
        let message = '';
        let followUps: string[] = [];
        let webSources: WebSourceResult[] = Array.isArray(resp?.webResults) ? resp.webResults.map((item: any) => ({
          title: item.title || 'Source web',
          url: item.url || '#',
          snippet: item.snippet || '',
          imageUrl: item.imageUrl || item.thumbnail || ''
        })) : [];
        let enrichment: Array<{ title?: string; website?: string; phone?: string; address?: string; imageUrl?: string; sourceUrl?: string; note?: string }> = Array.isArray(resp?.enrichment) ? resp.enrichment : [];

        const modelResp = resp && resp.data ? resp.data : resp;

        try {
          const choiceText = modelResp && Array.isArray(modelResp.choices) && modelResp.choices[0] && modelResp.choices[0].message
            ? modelResp.choices[0].message.content
            : undefined;

          let contentText = choiceText ||
            (typeof modelResp === 'string' ? modelResp : '') ||
            (modelResp && modelResp.output_text) ||
            (modelResp && modelResp.output && typeof modelResp.output === 'string' ? modelResp.output : '') ||
            (modelResp && modelResp.text) ||
            '';

          if (contentText) {
            const fencedJsonMatch = contentText.match(/```json\s*([\s\S]*?)\s*```/i) || contentText.match(/```\s*([\s\S]*?)\s*```/i);
            const jsonObjectMatch = contentText.match(/\{[\s\S]*"RESULTS"\s*:[\s\S]*\}/i) || contentText.match(/\{[\s\S]*"followUps"\s*:[\s\S]*\}/i);

            if (fencedJsonMatch) {
              const jsonString = fencedJsonMatch[1] || fencedJsonMatch[0];
              try {
                const parsed = JSON.parse(jsonString);
                if (parsed && Array.isArray(parsed.RESULTS)) {
                  recs = parsed.RESULTS.map((r: any) => this.hydrateRecommendation(r));
                  if (Array.isArray(parsed.followUps)) followUps = parsed.followUps;
                }
              } catch (e) {
                // ignore parse errors and continue with text fallback
              }
            } else if (jsonObjectMatch) {
              try {
                const parsed = JSON.parse(jsonObjectMatch[0]);
                if (parsed && Array.isArray(parsed.RESULTS)) {
                  recs = parsed.RESULTS.map((r: any) => this.hydrateRecommendation(r));
                  if (Array.isArray(parsed.followUps)) followUps = parsed.followUps;
                }
              } catch (e) {
                // ignore parse errors and continue with text fallback
              }
            }

            if (!message) {
              const cleaned = contentText.replace(/```json\s*|```/gi, '').trim();
              const plainText = cleaned.replace(/\{[\s\S]*\}/g, '').trim();
              message = plainText || cleaned;
            }
          }

          if (!recs.length && typeof modelResp === 'object' && modelResp !== null) {
            const possibleResults = modelResp.RESULTS || modelResp.results || modelResp.data || modelResp.output?.RESULTS;
            if (possibleResults) {
              let arr = possibleResults;
              if (typeof arr === 'string') {
                try { arr = JSON.parse(arr); } catch (e) { arr = null; }
              }
              if (Array.isArray(arr)) {
                recs = arr.map((r: any) => this.hydrateRecommendation(r));
              }
            }
            if (Array.isArray(modelResp.followUps)) followUps = modelResp.followUps;
            if (Array.isArray((modelResp as any).suggestedFollowUps)) followUps = (modelResp as any).suggestedFollowUps;
          }
        } catch (e) {
          // parsing errors should not block the response
        }

        if (/price|prix|budget|coût|cost|tarif|combien/i.test(userPrompt) && recs.length && !message.toLowerCase().includes('prix')) {
          const priceText = recs
            .slice(0, 3)
            .map((item) => `${item.title}: ${item.estimatedCostPerDay ? `${item.estimatedCostPerDay} TND/jour` : 'Tarif à vérifier'}`)
            .join(' • ');
          message = message ? `${message}\n\n💰 Estimation: ${priceText}` : `💰 Estimation: ${priceText}`;
        }

        if (enrichment.length) {
          const detailText = enrichment
            .map((item: any) => {
              const fields = [item.website, item.phone, item.address].filter(Boolean);
              return `• ${item.title || 'Lieu'}: ${fields.join(' • ') || item.note || 'Aucune information vérifiée trouvée'}`;
            })
            .join('\n');
          message = message ? `${message}\n\nInformations complémentaires :\n${detailText}` : `Informations complémentaires :\n${detailText}`;
        }

        if (!message) {
          message = `✨ Voici des recommandations personnalisées.`;
        }

        return { message, recommendations: recs, followUps, webSources, enrichment };
      }),
      // fallback to the existing local generator if the proxy is unreachable or returns an error
      catchError(() => this.generateBotResponseLocal(userPrompt, preferences))
    );
  }

  private generateBotResponseLocal(userPrompt: string, preferences?: UserPreferences): Observable<{
    message: string;
    recommendations: Recommendation[];
    followUps: string[];
    webSources: WebSourceResult[];
    enrichment: Array<{ title?: string; website?: string; phone?: string; address?: string; imageUrl?: string; sourceUrl?: string; note?: string }>;
  }> {
    const q = (userPrompt || '').toLowerCase();

    return new Observable(observer => {
      this.recommendDestinations(userPrompt, preferences).subscribe((recs: Recommendation[]) => {
        let text = '';
        let followUps: string[] = [];

        if (q.includes('plage') || q.includes('mer') || q.includes('baign')) {
          text = `🏖️ **Merveilleux choix pour le farniente !**\n\nJ'ai sélectionné pour vous les plus belles eaux turquoise de Tunisie. ${recs[0] ? '**' + recs[0].title + '** offre un cadre balnéaire parfait avec soleil garanti et plages de sable fin.' : ''}`;
          followUps = ['Où trouver les meilleurs hôtels les pieds dans l’eau ?', 'Quelles sont les activités nautiques ?', 'Générer un itinéraire 3 jours'];
        } else if (q.includes('désert') || q.includes('sahara') || q.includes('oasis')) {
          text = `🏜️ **Préparez-vous pour une aventure saharienne inoubliable !**\n\nEntre dunes dorées géantes, oasis de palmiers et bivouac étoilé, voici les escales magiques recommandées par l’IA.`;
          followUps = ['Quelle est la meilleure période ?', 'Comment réserver un safari 4x4 et nuit sous tente ?', 'Budget estimé pour 4 jours'];
        } else if (q.includes('histoire') || q.includes('culture') || q.includes('musée') || q.includes('romain')) {
          text = `🏛️ **La Tunisie recèle plus de 3 000 ans d’histoire méditerranéenne !**\n\nJ’ai repéré ces chefs-d’œuvre classés au patrimoine mondial de l’UNESCO, parfaits pour les passionnés d’archéologie et de légendes.`;
          followUps = ['Visite avec guide officiel', 'Festivals et événements culturels', 'Spécialités culinaires du terroir'];
        } else if (q.includes('randonnée') || q.includes('nature') || q.includes('montagne') || q.includes('vert')) {
          text = `🌲 **Cap sur le grand air et les trésors de verdure !**\n\nPour une immersion écotouristique entre forêts de chênes-lièges, montagnes et cascades, voici les joyaux naturels idéaux.`;
          followUps = ['Circuits de randonnée balisés', 'Hébergements éco-responsables', 'Climat et équipement conseillé'];
        } else if (q.includes('famille') || q.includes('enfant')) {
          text = `👨‍👩‍👧‍👦 **Voyage en famille réussi garanti !**\n\nVoici des destinations douces, sécurisées et riches en activités ludiques pour petits et grands.`;
          followUps = ['Clubs et parcs aquatiques pour enfants', 'Excursions adaptées en famille', 'Meilleures plages d’eau calme'];
        } else {
          text = `✨ **Voici vos recommandations sur-mesure !**\n\nJ’ai analysé vos critères d’exploration. Cliquez sur une destination pour l’afficher sur la carte ou générer son programme 3 jours.`;
          followUps = ['Affiner avec mon budget', 'Localiser sur la carte interactive', 'Découvrir un fait insolite'];
        }

        observer.next({
          message: text,
          recommendations: recs,
          followUps,
          webSources: [],
          enrichment: []
        });
        observer.complete();
      });
    });
  }

  getTouristForecast(region: string, period: string): Observable<ForecastResult> {
    const mock: ForecastResult = { region, period, values: [] };
    return of(mock);
  }

  detectTrends(text: string): Observable<TrendResult> {
    const mock: TrendResult = { topics: [] };
    return of(mock);
  }

  getAlerts(): Observable<any[]> {
    return of([]);
  }
}
