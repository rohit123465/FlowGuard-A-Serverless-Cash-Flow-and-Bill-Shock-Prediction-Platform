import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
  type CognitoUserSession,
} from "amazon-cognito-identity-js";
import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

interface AuthUser {
  username: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  signIn(email: string, password: string): Promise<void>;
  signOut(): void;
  getAccessToken(): Promise<string>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const clientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID;

if (!userPoolId || !clientId) {
  throw new Error("Cognito environment variables are not configured");
}

const userPool = new CognitoUserPool({ UserPoolId: userPoolId, ClientId: clientId });

function sessionFor(user: CognitoUser): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    user.getSession((error: Error | null, session: CognitoUserSession | null) => {
      if (error || !session?.isValid()) {
        reject(error ?? new Error("Your session has expired"));
        return;
      }
      resolve(session);
    });
  });
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentUser = userPool.getCurrentUser();
    if (!currentUser) {
      setLoading(false);
      return;
    }
    sessionFor(currentUser)
      .then(() => setUser({ username: currentUser.getUsername() }))
      .catch(() => currentUser.signOut())
      .finally(() => setLoading(false));
  }, []);

  const signIn = useCallback((email: string, password: string) => {
    const cognitoUser = new CognitoUser({ Username: email, Pool: userPool });
    const details = new AuthenticationDetails({ Username: email, Password: password });
    return new Promise<void>((resolve, reject) => {
      cognitoUser.authenticateUser(details, {
        onSuccess: () => {
          setUser({ username: cognitoUser.getUsername() });
          resolve();
        },
        onFailure: reject,
        newPasswordRequired: () => {
          cognitoUser.signOut();
          reject(new Error("A permanent password must be set before signing in."));
        },
      });
    });
  }, []);

  const signOut = useCallback(() => {
    userPool.getCurrentUser()?.signOut();
    setUser(null);
  }, []);

  const getAccessToken = useCallback(async () => {
    const currentUser = userPool.getCurrentUser();
    if (!currentUser) {
      throw new Error("You are not signed in");
    }
    const session = await sessionFor(currentUser);
    return session.getAccessToken().getJwtToken();
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signOut, getAccessToken }),
    [user, loading, signIn, signOut, getAccessToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
