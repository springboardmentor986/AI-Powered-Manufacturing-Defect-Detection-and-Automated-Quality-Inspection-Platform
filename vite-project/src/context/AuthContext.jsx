import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

const AuthContext = createContext(null);

const API_URL = "http://127.0.0.1:8000";


export function AuthProvider({ children }) {

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);


  

  useEffect(() => {

    const token =
      localStorage.getItem("access_token");


    if (!token) {

      setLoading(false);

      return;
    }


    const checkUser = async () => {

      try {

        const response = await fetch(
          `${API_URL}/auth/me`,
          {
            method: "GET",

            headers: {
              Authorization: `Bearer ${token}`,
              Accept: "application/json",
            },
          }
        );


        if (!response.ok) {

          throw new Error(
            "Session expired. Please login again."
          );
        }


        const data =
          await response.json();


        setUser(data);

      } catch (error) {

        console.error(
          "Authentication check failed:",
          error
        );


        localStorage.removeItem(
          "access_token"
        );

        setUser(null);

      } finally {

        setLoading(false);
      }
    };


    checkUser();

  }, []);



  const login = async (
    email,
    password
  ) => {

    try {

      const response = await fetch(
        `${API_URL}/auth/login`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },

          body: JSON.stringify({
            email: email,
            password: password,
          }),
        }
      );


      

      if (!response.ok) {

        let errorMessage =
          "Login failed.";

        try {

          const errorData =
            await response.json();

          errorMessage =
            errorData.detail ||
            errorMessage;

        } catch {
          // Response was not JSON
        }


        throw new Error(
          errorMessage
        );
      }


      

      const data =
        await response.json();


      console.log(
        "Login successful:",
        data
      );


      

      if (!data.access_token) {

        throw new Error(
          "Login succeeded but no access token was returned."
        );
      }


      

      localStorage.setItem(
        "access_token",
        data.access_token
      );


      

      if (data.user) {

        setUser(data.user);

        return data.user;
      }


      
      const userResponse =
        await fetch(
          `${API_URL}/auth/me`,
          {
            method: "GET",

            headers: {
              Authorization:
                `Bearer ${data.access_token}`,

              Accept: "application/json",
            },
          }
        );


      if (!userResponse.ok) {

        throw new Error(
          "Unable to fetch user information."
        );
      }


      const userData =
        await userResponse.json();


      setUser(userData);

      return userData;

    } catch (error) {

      console.error(
        "Login error:",
        error
      );


      

      if (
        error instanceof TypeError &&
        error.message === "Failed to fetch"
      ) {

        throw new Error(
          "Cannot connect to VisionInspect AI server. Make sure FastAPI is running on http://127.0.0.1:8000."
        );
      }


      throw error;
    }
  };


  
  const logout = () => {

    localStorage.removeItem(
      "access_token"
    );

    setUser(null);
  };


  
  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}




export function useAuth() {

  const context =
    useContext(AuthContext);


  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }


  return context;
}