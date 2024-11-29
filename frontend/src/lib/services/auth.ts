import { 
  signInWithPopup, 
  GoogleAuthProvider, 
  FacebookAuthProvider,
  signOut,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword
} from 'firebase/auth'
import { auth } from '@/lib/firebase'

const googleProvider = new GoogleAuthProvider()
const facebookProvider = new FacebookAuthProvider()

export const authService = {
  // Google Sign in
  signInWithGoogle: async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider)
      return result.user
    } catch (error) {
      throw error
    }
  },

  // Facebook Sign in
  signInWithFacebook: async () => {
    try {
      const result = await signInWithPopup(auth, facebookProvider)
      return result.user
    } catch (error) {
      throw error
    }
  },

  // Email/Password Sign up
  signUpWithEmail: async (email: string, password: string) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      return result.user
    } catch (error) {
      throw error
    }
  },

  // Email/Password Sign in
  signInWithEmail: async (email: string, password: string) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      return result.user
    } catch (error) {
      throw error
    }
  },

  // Sign out
  signOut: async () => {
    try {
      await signOut(auth)
    } catch (error) {
      throw error
    }
  }
} 