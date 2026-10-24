import React from 'react';
import {renderToString} from 'react-dom/server';
import {MemoryRouter} from 'react-router-dom';
import App from './App';
export function render(path:string){return renderToString(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>)}
