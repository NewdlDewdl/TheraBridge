/**
 * Auth Callback Route
 * Handles OAuth redirects from Supabase (Google, etc.)
 *
 * Flow for first-time OAuth users:
 * 1. User completes OAuth with Google
 * 2. Check if email is verified
 * 3. If not verified (first time), send verification email and redirect to code entry
 * 4. If verified (returning user), go to dashboard
 */

import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const error = requestUrl.searchParams.get('error');
  const errorDescription = requestUrl.searchParams.get('error_description');

  // Handle OAuth errors
  if (error) {
    console.error('Auth error:', error, errorDescription);
    const loginUrl = new URL('/auth/login', requestUrl.origin);
    loginUrl.searchParams.set('error', errorDescription || error);
    return NextResponse.redirect(loginUrl);
  }

  if (!code) {
    return NextResponse.redirect(new URL('/auth/login', requestUrl.origin));
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  try {
    // Exchange code for session
    const { data: sessionData, error: sessionError } = await supabase.auth.exchangeCodeForSession(code);

    if (sessionError || !sessionData.session) {
      console.error('Session exchange error:', sessionError);
      const loginUrl = new URL('/auth/login', requestUrl.origin);
      loginUrl.searchParams.set('error', 'Failed to authenticate');
      return NextResponse.redirect(loginUrl);
    }

    const user = sessionData.user;

    // Check if this is an OAuth user
    const provider = user.app_metadata?.provider;
    const isOAuthUser = provider && provider !== 'email';

    if (isOAuthUser) {
      // Check if user has verified their email before
      // We use a custom metadata flag to track this
      const hasVerifiedBefore = user.user_metadata?.oauth_verified === true;

      if (!hasVerifiedBefore) {
        // First-time OAuth user - needs to verify email
        // Send verification email
        const { error: verifyError } = await supabase.auth.resend({
          type: 'signup',
          email: user.email!,
        });

        if (verifyError) {
          console.error('Failed to send verification email:', verifyError);
        }

        // Redirect to login page with instruction to check email
        const loginUrl = new URL('/auth/login', requestUrl.origin);
        loginUrl.searchParams.set('step', 'enterCode');
        loginUrl.searchParams.set('email', user.email!);
        loginUrl.searchParams.set('oauth', 'true');
        return NextResponse.redirect(loginUrl);
      }

      // Returning OAuth user - already verified, go to dashboard
      return NextResponse.redirect(new URL('/patient/dashboard-v3', requestUrl.origin));
    }

    // Email/password user - go to dashboard
    return NextResponse.redirect(new URL('/patient/dashboard-v3', requestUrl.origin));

  } catch (err) {
    console.error('Callback error:', err);
    const loginUrl = new URL('/auth/login', requestUrl.origin);
    loginUrl.searchParams.set('error', 'Authentication failed');
    return NextResponse.redirect(loginUrl);
  }
}
