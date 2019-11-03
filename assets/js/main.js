import 'bootstrap';
import 'select2';
import axios from 'axios';
import $ from 'jquery'
import Sortable from 'sortablejs/modular/sortable.complete.esm.js';
import flatpickr from "flatpickr";
import moment from "moment";

import '../css/main.scss'


function itsworks() {
    console.log('its works');
}

window.$ = window.jQuery = $;
window.Sortable = Sortable;
window.axios = axios;
window.flatpickr = flatpickr;
window.moment = moment;

export const er = itsworks;