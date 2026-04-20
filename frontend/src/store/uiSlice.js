// src/store/uiSlice.js

import { createSlice } from '@reduxjs/toolkit'

// ─────────────────────────────────────────────
// UI SLICE
//
// Manages global UI state:
// - Cart drawer (slide-in panel) — Week 5
// - Modal state — as needed
// ─────────────────────────────────────────────
const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    cartDrawerOpen: false,
  },
  reducers: {
    openCartDrawer:   (state) => { state.cartDrawerOpen = true },
    closeCartDrawer:  (state) => { state.cartDrawerOpen = false },
    toggleCartDrawer: (state) => { state.cartDrawerOpen = !state.cartDrawerOpen },
  },
})

export const {
  openCartDrawer,
  closeCartDrawer,
  toggleCartDrawer,
} = uiSlice.actions

export const selectCartDrawerOpen = (state) => state.ui.cartDrawerOpen

export default uiSlice.reducer