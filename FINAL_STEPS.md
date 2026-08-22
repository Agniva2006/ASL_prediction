# 🚀 Sign0 Final Production Steps Checklist

This document contains the exact steps required to transform this application from a local testing environment into a fully deployed, monetized, "real" SaaS product. The codebase architecture (SQLAlchemy, HttpOnly Cookies, Stripe SDK) is already fully implemented and waiting for these final operational steps.

---

## 1. Get Your Real Stripe Credentials
Right now, the app works using a fallback "mock sandbox". To accept real money, you need to link your real Stripe account.

- [ ] **Create a Stripe Account:** Go to [Stripe.com](https://stripe.com) and sign up.
- [ ] **Get Your API Key:** 
  1. In the Stripe Dashboard, turn on **Test Mode** (toggle in the top right).
  2. Go to **Developers -> API keys**.
  3. Reveal and copy your **Secret Key** (`sk_test_...`).
  4. Paste this into your `.env` file as `STRIPE_API_KEY`.
- [ ] **Create Your Products:**
  1. Go to **Product Catalog -> Products** and click **Add product**.
  2. Create **Pro Learner** ($9.00/month). Save the resulting Price ID (`price_1Pxyz...`) to your `.env` file as `STRIPE_PRICE_PRO`.
  3. Create **Developer** ($49.00/month). Save the resulting Price ID to your `.env` file as `STRIPE_PRICE_DEVELOPER`.
- [ ] **Set Up Your Webhook:**
  1. Go to **Developers -> Webhooks** and click **Add endpoint**.
  2. The endpoint URL will be `https://your-production-domain.com/payment/webhook`.
  3. Listen to these events: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`.
  4. Save, then reveal the **Signing Secret** (`whsec_...`) and paste it into your `.env` file as `STRIPE_WEBHOOK_SECRET`.

## 2. Generate a Production Security Key
Right now, the JWT tokens are signed using a default or temporary key. You must replace this in production.

- [ ] **Generate the Key:** Open your terminal and run:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Save the Key:** Copy the long random string and paste it into your `.env` file as `SIGN0_SECRET_KEY`.

## 3. Set Up a Cloud Database (PostgreSQL)
The application currently uses a local SQLite database (`backend/data/sign0.db`). SQLite is great for local testing, but it will be wiped out if deployed to ephemeral cloud platforms like Render or Heroku.

- [ ] **Provision a Database:** Sign up for a cloud database provider like **Neon.tech**, **Supabase**, or **Render PostgreSQL**.
- [ ] **Get the Connection String:** Your provider will give you a database URL that looks like `postgresql://username:password@hostname:5432/dbname`.
- [ ] **Connect the App:** Paste this URL into your `.env` file as `DATABASE_URL`. The application will automatically detect it and migrate the tables to the cloud!

## 4. Deploy the Application
Your app is ready for the internet.

- [ ] **Push to GitHub:** Commit all your files to a GitHub repository (note that your `.env` file is safely ignored thanks to the `.gitignore`).
- [ ] **Deploy to Render (or Heroku):**
  1. Connect your GitHub repository to Render as a "Web Service".
  2. **Build Command:** `pip install -r backend/requirements.txt`
  3. **Start Command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
  4. **Environment Variables:** Crucially, copy all the variables from your local `.env` file into the "Environment Variables" section on the Render dashboard.

## 5. Domain Name & HTTPS
- [ ] **Buy a Domain:** Purchase a domain (e.g., `sign0.ai`) from Namecheap or Google Domains.
- [ ] **Link Domain:** In Render, go to your Web Service settings -> **Custom Domains**, add your domain, and follow the DNS configuration instructions.
- [ ] **Update Frontend API URL:** In `frontend/api.js`, change `REMOTE_API_BASE` to `https://api.your-domain.com` (or whatever your final URL is) and ensure `activeApiBaseUrl` points to it.

---

Once you complete these 5 steps, you will have a highly secure, real SaaS business capable of onboarding real users and accepting real credit card payments securely!
