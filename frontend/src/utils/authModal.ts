import { reactive } from 'vue';

export type AuthMode = 'login' | 'register' | 'reset';

interface AuthModalState {
  open: boolean;
  mode: AuthMode;
  reason: string;
}

export const authModalState = reactive<AuthModalState>({
  open: false,
  mode: 'login',
  reason: ''
});

export const openAuthModal = (mode: AuthMode = 'login', reason = '') => {
  authModalState.open = true;
  authModalState.mode = mode;
  authModalState.reason = reason;
};

export const switchAuthMode = (mode: AuthMode) => {
  authModalState.mode = mode;
};

export const closeAuthModal = () => {
  authModalState.open = false;
  authModalState.mode = 'login';
  authModalState.reason = '';
};
