import { Component, ViewChild, ElementRef, AfterViewChecked, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { NavbarComponent } from '../../layout/navbar/navbar.component';
import { FooterComponent } from '../../layout/footer/footer.component';
import {
  ModelIntegrationService,
  Recommendation,
  ChatMessage,
  UserPreferences
} from '../../../shared/services/model-integration.service';

export interface DayPlan {
  day: number;
  period: string;
  title: string;
  activities: string[];
}

@Component({
  selector: 'app-public-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, NavbarComponent, FooterComponent],
  templateUrl: './public-page.component.html',
  styleUrls: ['./public-page.component.scss']
})
export class PublicPageComponent implements OnInit, AfterViewChecked {
  @ViewChild('chatWindowRef') chatWindowRef!: ElementRef<HTMLElement>;
  @ViewChild('textareaRef') textareaRef!: ElementRef<HTMLTextAreaElement>;

  // État du Chat
  userInput = '';
  messages: ChatMessage[] = [];
  loading = false;
  isSurprising = false;
  activePanelTab: 'details' | 'map' | 'itinerary' | 'calculator' | 'saved' = 'details';

  // Données de Recommandation & Explorateur
  recommendations: Recommendation[] = [];
  allDestinations: Recommendation[] = [];
  selectedRecommendation: Recommendation | null = null;
  savedDestinations: Recommendation[] = [];
  readonly destinationImages: Record<Recommendation['category'], string> = {
    mer: '/images/destinations/mer.svg',
    sahara: '/images/destinations/sahara.svg',
    culture: '/images/destinations/culture.svg',
    nature: '/images/destinations/nature.svg',
    'bien-etre': '/images/destinations/bien-etre.svg'
  };
  exploredDestinationsSet = new Set<string>();
  generatedItinerary: DayPlan[] = [];

  // Simulateur de Budget Voyage
  tripDays = 3;
  travelersCount = 2;

  // Carte interactive
  mapUrl?: SafeResourceUrl;

  // Filtres et Préférences Voyageur
  governorates = [
    'Tous',
    'Tunis',
    'Medenine',
    'Tozeur',
    'Nabeul',
    'Jendouba',
    'Mahdia',
    'Kebili',
    'Bizerte'
  ];

  vibes = [
    { id: 'Tous', label: 'Toutes les envies', icon: '✨' },
    { id: 'mer', label: 'Plage & Eau turquoise', icon: '🏖️' },
    { id: 'sahara', label: 'Sahara & Oasis', icon: '🏜️' },
    { id: 'culture', label: 'Histoire & UNESCO', icon: '🏛️' },
    { id: 'nature', label: 'Nature & Montagne', icon: '🌲' },
    { id: 'bien-etre', label: 'Thalasso & Détente', icon: '💆' }
  ];

  budgetOptions = ['Tous', 'Économique', 'Modéré', 'Luxe'];
  travelerOptions = ['Solo (1)', 'En couple (2)', 'Famille (3-4)', 'Groupe d’amis (4+)'];

  selectedGovernorate = 'Tous';
  selectedVibe = 'Tous';
  selectedBudget = 'Tous';
  selectedTravelers = 'En couple (2)';

  quickSuggestions = [
    '☀️ Plages calmes et eau turquoise en famille',
    '🏜️ Aventure dans le Sahara avec nuit sous tente',
    '🏛️ Patrimoine antique, médina et artisanat',
    '🌲 Randonnée fraîcheur et nature au vert',
    '💆 Séjour thalasso et détente de luxe',
    '🍢 Meilleure gastronomie et spécialités du terroir'
  ];

  private shouldScroll = false;

  constructor(
    private modelService: ModelIntegrationService,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    this.setDefaultMap();
    this.loadSavedDestinations();
    this.loadChatHistory();

    this.modelService.getAllDestinations().subscribe(destinations => {
      this.allDestinations = destinations;
      if (this.messages.length === 0) {
        this.initWelcomeMessage();
      } else {
        const lastBotMsg = [...this.messages].reverse().find(m => m.from === 'bot' && m.recommendations?.length);
        if (lastBotMsg && lastBotMsg.recommendations && lastBotMsg.recommendations.length > 0) {
          this.recommendations = lastBotMsg.recommendations;
          this.selectRecommendation(this.recommendations[0], false);
        } else {
          this.loadDefaultRecommendations();
        }
      }
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  /**
   * Message de bienvenue engageant & personnalisé
   */
  initWelcomeMessage(): void {
    const welcomeMsg: ChatMessage = {
      id: 'msg-welcome',
      from: 'bot',
      text: 'Salam & Bienvenue sur **TouriSense.AI** ! 🇹🇳✨\n\nJe suis votre **compagnon de voyage intelligent**. Dites-moi ce dont vous rêvez pour votre séjour (détente en bord de mer, aventure dans les dunes, trésors archéologiques ou échappée gourmande), et je vous guiderai vers les plus belles pépites de Tunisie !',
      time: new Date().toISOString(),
      avatar: '🤖',
      suggestedFollowUps: [
        '🏖️ Plages paradisiaques & farniente',
        '🏜️ Expédition dans le Sahara & Oasis',
        '🏛️ Histoire antique & Médinas UNESCO',
        '🎲 Surprenez-moi avec un lieu insolite !'
      ]
    };
    this.messages = [welcomeMsg];
    this.saveChatHistory();
    this.loadDefaultRecommendations();
  }

  loadDefaultRecommendations(): void {
    this.recommendations = this.allDestinations.slice(0, 4);
    if (this.recommendations.length > 0) {
      this.selectRecommendation(this.recommendations[0], false);
    }
  }

  /**
   * Envoi du message utilisateur vers l'IA
   */
  send(): void {
    const text = (this.userInput || '').trim();
    if (!text || this.loading) return;

    const userMessage: ChatMessage = {
      id: 'msg-' + Date.now(),
      from: 'user',
      text: text,
      time: new Date().toISOString(),
      avatar: '👤'
    };

    this.messages.push(userMessage);
    this.userInput = '';
    this.loading = true;
    this.shouldScroll = true;
    this.saveChatHistory();

    const preferences: UserPreferences = {
      governorate: this.selectedGovernorate,
      vibe: this.selectedVibe !== 'Tous' ? this.selectedVibe : undefined,
      budget: this.selectedBudget !== 'Tous' ? this.selectedBudget : undefined,
      travelers: this.selectedTravelers
    };

    this.modelService.generateBotResponse(text, preferences).subscribe({
      next: (res) => {
        this.recommendations = res.recommendations;

        const botMessage: ChatMessage = {
          id: 'msg-' + Date.now(),
          from: 'bot',
          text: res.message,
          time: new Date().toISOString(),
          avatar: '🤖',
          recommendations: res.recommendations,
          suggestedFollowUps: res.followUps,
          webSources: res.webSources,
          enrichment: res.enrichment
        };

        this.messages.push(botMessage);
        this.loading = false;
        this.shouldScroll = true;
        this.saveChatHistory();

        if (res.recommendations.length > 0) {
          this.selectRecommendation(res.recommendations[0], false);
        }
      },
      error: () => {
        this.messages.push({
          id: 'msg-' + Date.now(),
          from: 'bot',
          text: 'Oups ! Une petite pause technique est survenue. Veuillez réessayer votre question.',
          time: new Date().toISOString(),
          avatar: '🤖'
        });
        this.loading = false;
        this.shouldScroll = true;
      }
    });
  }

  sendQuick(suggestion: string): void {
    if (suggestion.includes('Surprenez-moi')) {
      this.surpriseMe();
      return;
    }
    this.userInput = suggestion;
    this.send();
  }

  /**
   * Fonction ludique "🎲 Surprenez-moi !" (Boussole Magique)
   */
  surpriseMe(): void {
    if (this.allDestinations.length === 0 || this.loading) return;
    this.isSurprising = true;

    // Tire une destination au hasard différente de l'actuelle
    const candidates = this.allDestinations.filter(d => d.id !== this.selectedRecommendation?.id);
    const randomDest = candidates[Math.floor(Math.random() * candidates.length)] || this.allDestinations[0];

    const surpriseUserMsg: ChatMessage = {
      id: 'msg-' + Date.now(),
      from: 'user',
      text: '🎲 Lance la boussole magique et surprends-moi !',
      time: new Date().toISOString(),
      avatar: '👤'
    };
    this.messages.push(surpriseUserMsg);
    this.loading = true;
    this.shouldScroll = true;

    setTimeout(() => {
      this.recommendations = [randomDest];
      this.selectRecommendation(randomDest, true);

      const surpriseBotMsg: ChatMessage = {
        id: 'msg-' + Date.now(),
        from: 'bot',
        text: `✨ **Boussole magique activée !** 🧭\n\nJ'ai sélectionné pour vous : **${randomDest.title}** (${randomDest.governorate}) !\n\n💡 *Le saviez-vous ?* ${randomDest.funFact}`,
        time: new Date().toISOString(),
        avatar: '🤖',
        recommendations: [randomDest],
        suggestedFollowUps: [
          `Que faire à ${randomDest.title} ?`,
          `Quel est le budget pour 3 jours ?`,
          `Voir sur la carte interactive`
        ]
      };

      this.messages.push(surpriseBotMsg);
      this.loading = false;
      this.isSurprising = false;
      this.shouldScroll = true;
      this.saveChatHistory();
    }, 600);
  }

  /**
   * Sélection d'une destination avec suivi du "Passeport d'explorateur"
   */
  selectRecommendation(r: Recommendation, switchTab = true): void {
    this.selectedRecommendation = r;
    this.exploredDestinationsSet.add(r.id);
    this.updateMapForDestination(r);
    this.generateItinerary(r);

    if (switchTab) {
      this.activePanelTab = 'details';
    }
  }

  get exploredCount(): number {
    return this.exploredDestinationsSet.size;
  }

  get totalDestinationsCount(): number {
    return this.allDestinations.length || 9;
  }

  /**
   * Calcul du budget estimé live (Dinars & Euros)
   */
  get estimatedTotalBudgetTND(): number {
    if (!this.selectedRecommendation) return 0;
    return this.selectedRecommendation.estimatedCostPerDay * this.tripDays * this.travelersCount;
  }

  get estimatedTotalBudgetEUR(): number {
    // Taux approximatif 1 EUR ≈ 3.35 TND
    return Math.round(this.estimatedTotalBudgetTND / 3.35);
  }

  updateMapForDestination(r: Recommendation): void {
    if (r.lat != null && r.lon != null) {
      const lat = r.lat;
      const lon = r.lon;
      const delta = 0.08;
      const minLon = +(lon - delta).toFixed(4);
      const minLat = +(lat - delta).toFixed(4);
      const maxLon = +(lon + delta).toFixed(4);
      const maxLat = +(lat + delta).toFixed(4);

      const url = `https://www.openstreetmap.org/export/embed.html?bbox=${minLon},${minLat},${maxLon},${maxLat}&layer=mapnik&marker=${lat},${lon}`;
      this.mapUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
    }
  }

  setDefaultMap(): void {
    const minLon = 7.5;
    const minLat = 30.0;
    const maxLon = 11.9;
    const maxLat = 37.6;
    const url = `https://www.openstreetmap.org/export/embed.html?bbox=${minLon},${minLat},${maxLon},${maxLat}&layer=mapnik`;
    this.mapUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  generateItinerary(r: Recommendation): void {
    this.generatedItinerary = [
      {
        day: 1,
        period: 'Matin & Après-midi',
        title: `Immersion & découverte emblématique de ${r.title}`,
        activities: [
          `Arrivée et installation, premier tour panoramique dans ${r.title}`,
          r.highlights[0] || 'Visite guidée des points d’intérêt principaux',
          `Déjeuner typique : goûter à ${r.mustEatSpecialty}`
        ]
      },
      {
        day: 2,
        period: 'Journée d’aventure',
        title: `Expériences locales & trésors cachés`,
        activities: [
          r.highlights[1] || 'Excursion nature et exploration des environs',
          r.activities[0]?.title || 'Activité typique recommandée par l’IA',
          'Coucher de soleil panoramique et dîner aux spécialités du terroir'
        ]
      },
      {
        day: 3,
        period: 'Détente & artisanat',
        title: `Artisanat local, souvenirs & bien-être`,
        activities: [
          r.highlights[2] || 'Visite des souks et ateliers d’artisans traditionnels',
          'Temps libre pour la baignade, la relaxation ou la dégustation locale',
          'Clôture du séjour et préparation du carnet de voyage'
        ]
      }
    ];
  }

  toggleBookmark(r: Recommendation, ev?: Event): void {
    if (ev) ev.stopPropagation();
    const index = this.savedDestinations.findIndex(item => item.id === r.id);
    if (index > -1) {
      this.savedDestinations.splice(index, 1);
    } else {
      this.savedDestinations.push(r);
    }
    this.saveBookmarkedDestinations();
  }

  isBookmarked(r: Recommendation): boolean {
    return this.savedDestinations.some(item => item.id === r.id);
  }

  saveBookmarkedDestinations(): void {
    try {
      localStorage.setItem('touri_saved_destinations', JSON.stringify(this.savedDestinations));
    } catch (e) {}
  }

  loadSavedDestinations(): void {
    try {
      const raw = localStorage.getItem('touri_saved_destinations');
      if (raw) this.savedDestinations = JSON.parse(raw);
    } catch (e) {}
  }

  handleAction(actionType: 'activites' | 'itineraire' | 'carte' | 'budget', r: Recommendation): void {
    this.selectRecommendation(r, false);

    if (actionType === 'carte') {
      this.activePanelTab = 'map';
    } else if (actionType === 'itineraire') {
      this.activePanelTab = 'itinerary';
    } else if (actionType === 'budget') {
      this.activePanelTab = 'calculator';
    } else {
      this.activePanelTab = 'details';
    }

    const followPrompt = `${actionType === 'activites' ? 'Quelles sont les activités immanquables à' : actionType === 'budget' ? 'Détaille le budget pour' : 'Montre-moi l’itinéraire complet pour'} ${r.title}`;
    this.userInput = followPrompt;
    this.send();
  }

  onFilterChange(): void {
    const preferences: UserPreferences = {
      governorate: this.selectedGovernorate,
      vibe: this.selectedVibe !== 'Tous' ? this.selectedVibe : undefined,
      budget: this.selectedBudget !== 'Tous' ? this.selectedBudget : undefined,
      travelers: this.selectedTravelers
    };

    const currentQuery = this.userInput.trim() || 'destinations tunisiennes incontournables';
    this.modelService.recommendDestinations(currentQuery, preferences).subscribe(results => {
      this.recommendations = results;
      if (this.recommendations.length > 0) {
        this.selectRecommendation(this.recommendations[0], false);
      }
    });
  }

  handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  resetChat(): void {
    if (confirm('Voulez-vous réinitialiser votre session d’exploration ?')) {
      localStorage.removeItem('touri_chat_messages_v2');
      this.messages = [];
      this.initWelcomeMessage();
    }
  }

  exportTrip(): void {
    if (!this.selectedRecommendation) return;
    const r = this.selectedRecommendation;
    let exportText = `=======================================\n`;
    exportText += `🌍 PASSEPORT D'EXPLORATEUR TOURISENSE.AI\n`;
    exportText += `Destination : ${r.title} (${r.governorate})\n`;
    exportText += `Score de correspondance IA : ${r.matchScore}%\n`;
    exportText += `Spécialité culinaire : ${r.mustEatSpecialty}\n`;
    exportText += `Budget estimé : ~${this.estimatedTotalBudgetTND} DT pour ${this.tripDays} jours (${this.travelersCount} pers.)\n`;
    exportText += `Meilleure période : ${r.bestSeason}\n`;
    exportText += `---------------------------------------\n`;
    exportText += `LE SAVIEZ-VOUS ?\n${r.funFact}\n\n`;
    exportText += `POINTS FORTS :\n${r.highlights.map(h => '- ' + h).join('\n')}\n\n`;
    exportText += `PROGRAMME SUR-MESURE (3 JOURS) :\n`;
    this.generatedItinerary.forEach(d => {
      exportText += `Jour ${d.day} (${d.period}) - ${d.title}\n`;
      d.activities.forEach(a => exportText += `  • ${a}\n`);
    });
    exportText += `=======================================\n`;

    const blob = new Blob([exportText], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `TouriSense_Carnet_${r.id}.txt`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  scrollToBottom(): void {
    try {
      if (this.chatWindowRef) {
        const el = this.chatWindowRef.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    } catch (e) {}
  }

  saveChatHistory(): void {
    try {
      localStorage.setItem('touri_chat_messages_v2', JSON.stringify(this.messages));
    } catch (e) {}
  }

  loadChatHistory(): void {
    try {
      const raw = localStorage.getItem('touri_chat_messages_v2');
      if (raw) {
        this.messages = JSON.parse(raw);
      }
    } catch (e) {}
  }
}
