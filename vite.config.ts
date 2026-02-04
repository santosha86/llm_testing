// // import path from 'path';
// // import { defineConfig, loadEnv } from 'vite';
// // import react from '@vitejs/plugin-react';

// // export default defineConfig(({ mode }) => {
// //     const env = loadEnv(mode, '.', '');
// //     return {
// //       server: {
// //         port: 3000,
// //         host: '0.0.0.0',
// //         allowedHosts: true,
// //       },
// //       plugins: [react()],
// //       define: {
// //         'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
// //         'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
// //       },
// //       resolve: {
// //         alias: {
// //           '@': path.resolve(__dirname, '.'),
// //         }
// //       }
// //     };
// // });

// import path from 'path';
// import { defineConfig, loadEnv } from 'vite';
// import react from '@vitejs/plugin-react';

// export default defineConfig(({ mode }) => {
//   // Load environment variables based on the current mode (e.g., development or production)
//   const env = loadEnv(mode, '.', '');

//   return {
//     // Server configuration
//     server: {
//       port: 3000,            // Set the server to listen on port 3000
//       host: '0.0.0.0',       // Make the server accessible from any IP address
//       allowedHosts: true,    // Allow all hosts (can be more restrictive if needed)
//     },
//     // Plugins
//     plugins: [
//       react(),              // Enable React plugin for JSX support
//     ],
//     // Define global constants
//     define: {
//       'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
//       'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
//     },
//     // Resolve aliases (optional, for shorter import paths)
//     resolve: {
//       alias: {
//         '@': path.resolve(__dirname, '.'),  // Allows import like `import X from '@/path'`
//       },
//     },
//     // Base path for the app (important for deploying in subdirectories)
//     base: '/chatbot/',  // <--- important for deployment to a sub-path (e.g., example.com/chatbot)
//   };
// });

import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // Load environment variables based on the current mode (e.g., development or production)
  const env = loadEnv(mode, '.', '');

  return {
    // Server configuration
    server: {
      port: 3000,            // Set the server to listen on port 3000
      host: '0.0.0.0',       // Make the server accessible from any IP address
      allowedHosts: true,    // Allow all hosts (can be more restrictive if needed)
    },
    // Plugins
    plugins: [
      react(),              // Enable React plugin for JSX support
    ],
    // Define global constants
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    // Resolve aliases (optional, for shorter import paths)
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),  // Allows import like `import X from '@/path'`
      },
    },
    // Base path for the app (important for deploying in subdirectories)
    base: '/chatbot/',  // <--- important for deployment to a sub-path (e.g., example.com/chatbot)
  };
});