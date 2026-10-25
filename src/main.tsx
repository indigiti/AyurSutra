import React from 'react';
import {createRoot,hydrateRoot} from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import App from './App';
import './styles.css';
const root=document.getElementById('root')!;
const app=<React.StrictMode><BrowserRouter basename={import.meta.env.BASE_URL}><App/></BrowserRouter></React.StrictMode>;
if(root.hasChildNodes()) hydrateRoot(root,app); else createRoot(root).render(app);
if(import.meta.env.PROD && 'serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register(import.meta.env.BASE_URL+'sw.js', {scope:import.meta.env.BASE_URL}).catch(()=>{}));}
