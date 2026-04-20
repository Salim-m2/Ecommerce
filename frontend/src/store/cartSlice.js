// src/store/cartSlice.js

import { createSlice } from '@reduxjs/toolkit'

// ─────────────────────────────────────────────
// CART SLICE
//
// Only stores the cart item COUNT for the
// navbar badge. Full cart data lives on the
// server and is fetched via TanStack Query.
// Full cart functionality built in Week 5.
// ─────────────────────────────────────────────
const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    itemCount: 0,
  },
  reducers: {
    setCartCount: (state, action) => {
      state.itemCount = action.payload
    },
    incrementCartCount: (state) => {
      state.itemCount += 1
    },
    decrementCartCount: (state) => {
      state.itemCount = Math.max(0, state.itemCount - 1)
    },
    resetCartCount: (state) => {
      state.itemCount = 0
    },
  },
})

export const {
  setCartCount,
  incrementCartCount,
  decrementCartCount,
  resetCartCount,
} = cartSlice.actions

export const selectCartCount = (state) => state.cart.itemCount

export default cartSlice.reducer