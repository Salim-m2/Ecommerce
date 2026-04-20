// src/store/index.js

import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import cartReducer from './cartSlice'
import uiReducer   from './uiSlice'

const store = configureStore({
  reducer: {
    auth: authReducer,
    cart: cartReducer,
    ui:   uiReducer,
  },
})

export default store