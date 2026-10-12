export interface HeroStat {
  label: string;
  value: string;
}

export interface ModuleItem {
  title: string;
  description: string;
  tags: string[];
}

export interface SpaceItem {
  title: string;
  description: string;
  features: string[];
  route: string;
  accent: 'sand' | 'teal';
}
