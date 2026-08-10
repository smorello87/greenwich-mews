/// <reference types="astro/client" />

interface Window {
  openPersonModal: (person: any) => void;
  openItemModal: (item: any) => void;
  openProductionModal: (production: any) => void;
  openContributorModal: (contributor: any) => void;
}
