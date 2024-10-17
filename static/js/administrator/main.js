import 'flowbite';
import Chart from 'chart.js/auto';
import L from 'leaflet';
import AOS from 'aos';
import flatpickr from "flatpickr";
import anime from 'animejs/lib/anime.es.js';

// Initialize AOS
AOS.init();

// Make libraries available globally
window.Chart = Chart;
window.L = L;
window.flatpickr = flatpickr;
window.anime = anime;

// Administrator-specific JavaScript
// ... your code here ...