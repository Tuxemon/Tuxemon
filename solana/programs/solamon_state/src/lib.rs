use anchor_lang::prelude::*;

declare_id!("SoLaMoN1111111111111111111111111111111111111");

#[program]
pub mod solamon_state {
    use super::*;

    pub fn init_profile(ctx: Context<InitProfile>) -> Result<()> {
        let profile = &mut ctx.accounts.profile;
        profile.authority = ctx.accounts.authority.key();
        profile.level = 1;
        profile.experience = 0;
        profile.pending_sol_lamports = 0;
        profile.pending_spl_amount = 0;
        profile.bump = ctx.bumps.profile;
        Ok(())
    }

    pub fn set_profile_state(
        ctx: Context<SetProfileState>,
        level: u16,
        experience: u64,
    ) -> Result<()> {
        let profile = &mut ctx.accounts.profile;
        require_keys_eq!(profile.authority, ctx.accounts.authority.key(), SolamonError::Unauthorized);
        profile.level = level;
        profile.experience = experience;
        Ok(())
    }

    pub fn accrue_reward(
        ctx: Context<SetProfileState>,
        sol_lamports: u64,
        spl_amount: u64,
    ) -> Result<()> {
        let profile = &mut ctx.accounts.profile;
        require_keys_eq!(profile.authority, ctx.accounts.authority.key(), SolamonError::Unauthorized);
        profile.pending_sol_lamports = profile.pending_sol_lamports.saturating_add(sol_lamports);
        profile.pending_spl_amount = profile.pending_spl_amount.saturating_add(spl_amount);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitProfile<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        seeds = [b"profile", authority.key().as_ref()],
        bump,
        space = 8 + CharacterProfile::INIT_SPACE,
    )]
    pub profile: Account<'info, CharacterProfile>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SetProfileState<'info> {
    pub authority: Signer<'info>,
    #[account(
        mut,
        seeds = [b"profile", authority.key().as_ref()],
        bump = profile.bump,
    )]
    pub profile: Account<'info, CharacterProfile>,
}

#[account]
#[derive(InitSpace)]
pub struct CharacterProfile {
    pub authority: Pubkey,
    pub level: u16,
    pub experience: u64,
    pub pending_sol_lamports: u64,
    pub pending_spl_amount: u64,
    pub bump: u8,
}

#[error_code]
pub enum SolamonError {
    #[msg("Caller is not authorized for this profile")]
    Unauthorized,
}
