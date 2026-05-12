import { reactive } from 'vue';

export type AppDialogVariant = 'info' | 'success' | 'warning' | 'error';

export interface AppDialogOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: AppDialogVariant;
  showCancel?: boolean;
  dismissible?: boolean;
}

interface AppDialogState {
  open: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  variant: AppDialogVariant;
  showCancel: boolean;
  dismissible: boolean;
}

const defaultState = (): AppDialogState => ({
  open: false,
  title: '提示',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  variant: 'info',
  showCancel: false,
  dismissible: true
});

export const appDialogState = reactive<AppDialogState>(defaultState());

let pendingResolver: ((confirmed: boolean) => void) | null = null;

const resetDialogState = () => {
  Object.assign(appDialogState, defaultState());
};

const openDialog = (options: AppDialogOptions): Promise<boolean> => {
  if (pendingResolver) {
    pendingResolver(false);
    pendingResolver = null;
  }

  Object.assign(appDialogState, {
    open: true,
    title: options.title || '提示',
    message: options.message,
    confirmText: options.confirmText || '确定',
    cancelText: options.cancelText || '取消',
    variant: options.variant || 'info',
    showCancel: options.showCancel ?? false,
    dismissible: options.dismissible ?? true
  });

  return new Promise((resolve) => {
    pendingResolver = resolve;
  });
};

const finishDialog = (confirmed: boolean) => {
  const resolver = pendingResolver;
  pendingResolver = null;
  resetDialogState();
  resolver?.(confirmed);
};

export const showAppAlert = (message: string, options: Omit<AppDialogOptions, 'message' | 'showCancel'> = {}) => {
  return openDialog({
    ...options,
    message,
    showCancel: false
  });
};

export const showAppConfirm = (message: string, options: Omit<AppDialogOptions, 'message' | 'showCancel'> = {}) => {
  return openDialog({
    ...options,
    message,
    showCancel: true
  });
};

export const confirmAppDialog = () => {
  finishDialog(true);
};

export const cancelAppDialog = () => {
  finishDialog(false);
};

export const dismissAppDialog = () => {
  if (!appDialogState.dismissible) {
    return;
  }
  finishDialog(false);
};
