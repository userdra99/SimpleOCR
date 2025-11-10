# Gmail API Setup Guide

This guide will walk you through setting up Gmail API credentials for SimpleOCR.

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account (the one you want to use for Gmail access)
3. Click on the project dropdown at the top of the page
4. Click **"New Project"**
5. Enter a project name (e.g., "SimpleOCR" or "Gmail Receipt Extractor")
6. Click **"Create"**
7. Wait for the project to be created (usually takes a few seconds)
8. Make sure your new project is selected in the project dropdown

### Step 2: Enable Gmail API

1. In the Google Cloud Console, click the **☰ (hamburger menu)** in the top left
2. Navigate to **"APIs & Services"** > **"Library"**
3. In the search box, type **"Gmail API"**
4. Click on **"Gmail API"** from the results
5. Click the **"Enable"** button
6. Wait for the API to be enabled (usually instant)

### Step 3: Configure OAuth Consent Screen

1. In the Google Cloud Console, go to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** (unless you have a Google Workspace account, then you can use "Internal")
3. Click **"Create"**
4. Fill in the required information:
   - **App name**: "SimpleOCR" or any name you prefer
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"Save and Continue"**
6. On the "Scopes" page, click **"Add or Remove Scopes"**
7. Search for and select: **`https://www.googleapis.com/auth/gmail.readonly`**
   - This gives read-only access to Gmail (perfect for our use case)
8. Click **"Update"**, then **"Save and Continue"**
9. On the "Test users" page:
   - Click **"Add Users"**
   - Add your Gmail address (the one you want to access)
   - Click **"Add"**, then **"Save and Continue"**
10. Review the summary and click **"Back to Dashboard"**

**Note:** If you see a warning about "This app isn't verified", that's normal for personal projects. You can click "Advanced" > "Go to [Your App Name] (unsafe)" when testing.

### Step 4: Create OAuth 2.0 Credentials

1. In the Google Cloud Console, go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** at the top
3. Select **"OAuth client ID"**
4. If prompted, select **"Desktop app"** as the application type
5. Fill in the details:
   - **Name**: "SimpleOCR Desktop Client" (or any name)
   - **Application type**: **"Desktop app"** (should already be selected)
6. Click **"Create"**
7. A dialog will appear with your credentials. You'll see:
   - **Client ID** (long string)
   - **Client secret** (long string)
8. **IMPORTANT:** Click **"Download JSON"** button (this downloads the credentials file)
9. **Rename the downloaded file** to `credentials.json`
10. **Move the file** to your SimpleOCR project directory (`/home/dra/SimpleOCR/`)

### Step 5: Verify Credentials File

1. Make sure `credentials.json` is in your project root directory:
   ```bash
   ls -la /home/dra/SimpleOCR/credentials.json
   ```

2. The file should look something like this (don't worry if it's slightly different):
   ```json
   {
     "installed": {
       "client_id": "your-client-id.apps.googleusercontent.com",
       "project_id": "your-project-id",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "your-client-secret",
       "redirect_uris": ["http://localhost"]
     }
   }
   ```

### Step 6: Test the Setup

1. Make sure your virtual environment is activated:
   ```bash
   source activate.sh
   ```

2. Run the main script (it will prompt for authentication on first run):
   ```bash
   python main.py
   ```

3. On first run, you'll see:
   - A browser window will open automatically
   - You'll be asked to sign in with your Google account
   - You'll see a consent screen asking for permission to access Gmail
   - Click **"Allow"** or **"Continue"**
   - The browser may show "This app isn't verified" - click **"Advanced"** > **"Go to [Your App Name] (unsafe)"**
   - After granting permission, you'll see "The authentication flow has completed"

4. A new file `token.json` will be created in your project directory
   - This file stores your authentication token
   - You won't need to authenticate again unless the token expires

5. The script should now start processing your emails!

## Troubleshooting

### Issue: "Credentials file not found"

**Solution:**
- Make sure `credentials.json` is in the project root directory
- Check the file name is exactly `credentials.json` (case-sensitive)
- Verify the file path: `ls -la credentials.json`

### Issue: "Redirect URI mismatch"

**Solution:**
- Make sure you selected **"Desktop app"** as the application type
- Don't modify the redirect URIs in the credentials file
- The default `http://localhost` redirect URI is correct for desktop apps

### Issue: "Access blocked: This app's request is invalid"

**Solution:**
- Make sure you added your email as a test user in the OAuth consent screen
- If your app is in "Testing" mode, only test users can access it
- Make sure you're signing in with the same Google account you added as a test user

### Issue: "This app isn't verified" warning

**Solution:**
- This is normal for personal projects
- Click **"Advanced"** > **"Go to [Your App Name] (unsafe)"**
- For personal use, you don't need to verify the app through Google's verification process

### Issue: Browser doesn't open automatically

**Solution:**
- The script will print a URL in the terminal
- Copy and paste that URL into your browser manually
- Complete the authentication flow in the browser
- Copy the authorization code from the browser back to the terminal if prompted

### Issue: Token expires

**Solution:**
- Delete the `token.json` file
- Run the script again to re-authenticate
- The token should be valid for a long time, but if it expires, just re-authenticate

## Security Notes

1. **Never commit credentials.json or token.json to git**
   - These files are already in `.gitignore`
   - Keep them secure and private

2. **Credentials.json contains sensitive information**
   - Don't share this file with anyone
   - Don't post it online or in public repositories

3. **Token.json contains your authentication token**
   - This allows access to your Gmail account
   - Keep it secure

4. **The app only requests read-only access**
   - It can only read emails, not send or delete them
   - This is the safest permission level

## Quick Checklist

- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth consent screen configured
- [ ] Test user added (your Gmail address)
- [ ] OAuth 2.0 credentials created (Desktop app)
- [ ] credentials.json downloaded and placed in project root
- [ ] Virtual environment activated
- [ ] First authentication completed successfully
- [ ] token.json file created

## Next Steps

Once you have `credentials.json` in place and have completed the first authentication:

1. Run the application:
   ```bash
   python main.py
   ```

2. The script will:
   - Authenticate with Gmail (automatic after first time)
   - Search for receipt emails
   - Download and process attachments
   - Extract receipt data
   - Save to `receipts.json`

3. Check the output:
   ```bash
   cat receipts.json
   ```

## Need Help?

If you encounter issues:

1. Check the error message in the terminal
2. Review the troubleshooting section above
3. Verify all steps were completed correctly
4. Make sure you're using the correct Google account
5. Check that Gmail API is enabled in your project

## Additional Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

