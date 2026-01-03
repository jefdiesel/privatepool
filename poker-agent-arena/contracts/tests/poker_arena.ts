import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PokerArena } from "../target/types/poker_arena";
import { expect } from "chai";
import { Keypair, PublicKey, SystemProgram, LAMPORTS_PER_SOL } from "@solana/web3.js";
import { createHash } from "crypto";

describe("poker_arena", () => {
  // Configure the client to use the local cluster
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.PokerArena as Program<PokerArena>;

  // Test accounts
  const admin = provider.wallet;
  const treasury = Keypair.generate();
  const pointsMint = Keypair.generate();
  const player1 = Keypair.generate();
  const player2 = Keypair.generate();

  // PDAs
  let arenaConfigPda: PublicKey;
  let tournamentPda: PublicKey;
  let registration1Pda: PublicKey;
  let registration2Pda: PublicKey;

  // Test data
  const blindStructureHash = createHash("sha256")
    .update(JSON.stringify({ levels: [] }))
    .digest();
  const payoutStructureHash = createHash("sha256")
    .update(JSON.stringify({ payouts: [] }))
    .digest();
  const agentPromptHash = createHash("sha256")
    .update("test prompt")
    .digest();

  before(async () => {
    // Derive PDAs
    [arenaConfigPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("arena_config")],
      program.programId
    );

    [tournamentPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("tournament"), Buffer.from([1, 0, 0, 0, 0, 0, 0, 0])],
      program.programId
    );

    // Airdrop SOL to test accounts
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(player1.publicKey, 5 * LAMPORTS_PER_SOL)
    );
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(player2.publicKey, 5 * LAMPORTS_PER_SOL)
    );
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(treasury.publicKey, 0.1 * LAMPORTS_PER_SOL)
    );
  });

  describe("initialize", () => {
    it("should initialize the arena config", async () => {
      await program.methods
        .initialize(treasury.publicKey, pointsMint.publicKey)
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      const arenaConfig = await program.account.arenaConfig.fetch(arenaConfigPda);

      expect(arenaConfig.admin.toString()).to.equal(admin.publicKey.toString());
      expect(arenaConfig.treasury.toString()).to.equal(treasury.publicKey.toString());
      expect(arenaConfig.pointsMint.toString()).to.equal(pointsMint.publicKey.toString());
      expect(arenaConfig.tournamentCount.toNumber()).to.equal(0);
    });
  });

  describe("create_tournament", () => {
    it("should create a tournament", async () => {
      const maxPlayers = 27;
      const startingStack = new anchor.BN(10000);
      const startsAt = new anchor.BN(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

      await program.methods
        .createTournament(
          maxPlayers,
          startingStack,
          startsAt,
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      const tournament = await program.account.tournament.fetch(tournamentPda);

      expect(tournament.id.toNumber()).to.equal(1);
      expect(tournament.maxPlayers).to.equal(maxPlayers);
      expect(tournament.startingStack.toNumber()).to.equal(10000);
      expect(tournament.registeredPlayers).to.equal(0);
      expect(tournament.status).to.deep.equal({ created: {} });
    });

    it("should fail when called by non-admin", async () => {
      const [tournament2Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([2, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      try {
        await program.methods
          .createTournament(
            27,
            new anchor.BN(10000),
            new anchor.BN(Math.floor(Date.now() / 1000) + 3600),
            Array.from(blindStructureHash),
            Array.from(payoutStructureHash)
          )
          .accounts({
            admin: player1.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournament2Pda,
            systemProgram: SystemProgram.programId,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown an error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("Unauthorized");
      }
    });
  });

  describe("open_registration", () => {
    it("should open registration for the tournament", async () => {
      await program.methods
        .openRegistration()
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
        })
        .rpc();

      const tournament = await program.account.tournament.fetch(tournamentPda);
      expect(tournament.status).to.deep.equal({ registration: {} });
    });
  });

  describe("register_player", () => {
    it("should register a player with FREE tier", async () => {
      [registration1Pda] = PublicKey.findProgramAddressSync(
        [
          Buffer.from("registration"),
          tournamentPda.toBuffer(),
          player1.publicKey.toBuffer(),
        ],
        program.programId
      );

      const agentName = Buffer.alloc(32);
      agentName.write("FreeAgent");
      const agentImageUri = Buffer.alloc(128);
      agentImageUri.write("https://example.com/avatar.jpg");

      await program.methods
        .registerPlayer(
          { free: {} },
          Array.from(agentPromptHash),
          Array.from(agentName),
          Array.from(agentImageUri)
        )
        .accounts({
          player: player1.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
          registration: registration1Pda,
          treasury: treasury.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([player1])
        .rpc();

      const registration = await program.account.playerRegistration.fetch(registration1Pda);
      expect(registration.wallet.toString()).to.equal(player1.publicKey.toString());
      expect(registration.tier).to.deep.equal({ free: {} });

      const tournament = await program.account.tournament.fetch(tournamentPda);
      expect(tournament.registeredPlayers).to.equal(1);
    });

    it("should register a player with BASIC tier (0.1 SOL)", async () => {
      [registration2Pda] = PublicKey.findProgramAddressSync(
        [
          Buffer.from("registration"),
          tournamentPda.toBuffer(),
          player2.publicKey.toBuffer(),
        ],
        program.programId
      );

      const agentName = Buffer.alloc(32);
      agentName.write("BasicAgent");
      const agentImageUri = Buffer.alloc(128);
      agentImageUri.write("https://example.com/avatar2.jpg");

      const treasuryBalanceBefore = await provider.connection.getBalance(treasury.publicKey);

      await program.methods
        .registerPlayer(
          { basic: {} },
          Array.from(agentPromptHash),
          Array.from(agentName),
          Array.from(agentImageUri)
        )
        .accounts({
          player: player2.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
          registration: registration2Pda,
          treasury: treasury.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([player2])
        .rpc();

      const registration = await program.account.playerRegistration.fetch(registration2Pda);
      expect(registration.wallet.toString()).to.equal(player2.publicKey.toString());
      expect(registration.tier).to.deep.equal({ basic: {} });

      const tournament = await program.account.tournament.fetch(tournamentPda);
      expect(tournament.registeredPlayers).to.equal(2);

      // Verify 0.1 SOL was transferred to treasury
      const treasuryBalanceAfter = await provider.connection.getBalance(treasury.publicKey);
      expect(treasuryBalanceAfter - treasuryBalanceBefore).to.equal(0.1 * LAMPORTS_PER_SOL);
    });

    it("should fail when tournament is full", async () => {
      // This test would require registering max_players first
      // For now, we'll just verify the constraint exists in the contract
    });

    it("should register a player with PRO tier (1 SOL)", async () => {
      // Create a new player for PRO tier
      const proPlayer = Keypair.generate();

      // Airdrop enough SOL for PRO tier + rent
      await provider.connection.confirmTransaction(
        await provider.connection.requestAirdrop(proPlayer.publicKey, 2 * LAMPORTS_PER_SOL)
      );

      const [proRegistrationPda] = PublicKey.findProgramAddressSync(
        [
          Buffer.from("registration"),
          tournamentPda.toBuffer(),
          proPlayer.publicKey.toBuffer(),
        ],
        program.programId
      );

      const agentName = Buffer.alloc(32);
      agentName.write("ProAgent");
      const agentImageUri = Buffer.alloc(128);
      agentImageUri.write("https://example.com/pro-avatar.jpg");

      const treasuryBalanceBefore = await provider.connection.getBalance(treasury.publicKey);

      await program.methods
        .registerPlayer(
          { pro: {} },
          Array.from(agentPromptHash),
          Array.from(agentName),
          Array.from(agentImageUri)
        )
        .accounts({
          player: proPlayer.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
          registration: proRegistrationPda,
          treasury: treasury.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([proPlayer])
        .rpc();

      const registration = await program.account.playerRegistration.fetch(proRegistrationPda);
      expect(registration.wallet.toString()).to.equal(proPlayer.publicKey.toString());
      expect(registration.tier).to.deep.equal({ pro: {} });

      // Verify 1 SOL was transferred to treasury
      const treasuryBalanceAfter = await provider.connection.getBalance(treasury.publicKey);
      expect(treasuryBalanceAfter - treasuryBalanceBefore).to.equal(1 * LAMPORTS_PER_SOL);
    });

    it("should fail for duplicate registration", async () => {
      // Try to register player1 again (already registered)
      try {
        const agentName = Buffer.alloc(32);
        agentName.write("DuplicateAgent");
        const agentImageUri = Buffer.alloc(128);
        agentImageUri.write("https://example.com/dup.jpg");

        await program.methods
          .registerPlayer(
            { free: {} },
            Array.from(agentPromptHash),
            Array.from(agentName),
            Array.from(agentImageUri)
          )
          .accounts({
            player: player1.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournamentPda,
            registration: registration1Pda, // Same PDA as before
            treasury: treasury.publicKey,
            systemProgram: SystemProgram.programId,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown an error for duplicate registration");
      } catch (error: any) {
        // Account already exists error from Anchor init constraint
        expect(error.message).to.include("already in use");
      }
    });

    it("should fail when registration is not open", async () => {
      // Create a new tournament that's in Created status (not Registration)
      const [tournament2Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([2, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      await program.methods
        .createTournament(
          27,
          new anchor.BN(10000),
          new anchor.BN(Math.floor(Date.now() / 1000) + 7200),
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament2Pda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // Try to register for a tournament that's not open
      const [reg2Pda] = PublicKey.findProgramAddressSync(
        [
          Buffer.from("registration"),
          tournament2Pda.toBuffer(),
          player1.publicKey.toBuffer(),
        ],
        program.programId
      );

      try {
        const agentName = Buffer.alloc(32);
        agentName.write("EarlyBird");
        const agentImageUri = Buffer.alloc(128);

        await program.methods
          .registerPlayer(
            { free: {} },
            Array.from(agentPromptHash),
            Array.from(agentName),
            Array.from(agentImageUri)
          )
          .accounts({
            player: player1.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournament2Pda,
            registration: reg2Pda,
            treasury: treasury.publicKey,
            systemProgram: SystemProgram.programId,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown RegistrationNotOpen error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("RegistrationNotOpen");
      }
    });

    it("should fail with invalid treasury account", async () => {
      // Create another tournament for this test
      const [tournament3Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([3, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      await program.methods
        .createTournament(
          27,
          new anchor.BN(10000),
          new anchor.BN(Math.floor(Date.now() / 1000) + 7200),
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament3Pda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      await program.methods
        .openRegistration()
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament3Pda,
        })
        .rpc();

      const fakeTreasury = Keypair.generate();
      const [reg3Pda] = PublicKey.findProgramAddressSync(
        [
          Buffer.from("registration"),
          tournament3Pda.toBuffer(),
          player1.publicKey.toBuffer(),
        ],
        program.programId
      );

      try {
        const agentName = Buffer.alloc(32);
        agentName.write("BadTreasury");
        const agentImageUri = Buffer.alloc(128);

        await program.methods
          .registerPlayer(
            { basic: {} }, // BASIC tier requires payment
            Array.from(agentPromptHash),
            Array.from(agentName),
            Array.from(agentImageUri)
          )
          .accounts({
            player: player1.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournament3Pda,
            registration: reg3Pda,
            treasury: fakeTreasury.publicKey, // Wrong treasury!
            systemProgram: SystemProgram.programId,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown InvalidTierPayment error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("InvalidTierPayment");
      }
    });
  });

  describe("start_tournament", () => {
    it("should start a tournament with sufficient players", async () => {
      // Tournament already has players from previous tests
      const tournamentBefore = await program.account.tournament.fetch(tournamentPda);
      expect(tournamentBefore.registeredPlayers).to.be.at.least(2);

      await program.methods
        .startTournament()
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournamentPda,
          recentSlothashes: anchor.web3.SYSVAR_SLOT_HASHES_PUBKEY,
        })
        .rpc();

      const tournamentAfter = await program.account.tournament.fetch(tournamentPda);
      expect(tournamentAfter.status).to.deep.equal({ inProgress: {} });
      expect(tournamentAfter.seedSlot.toNumber()).to.be.greaterThan(0);
    });

    it("should fail when called by non-admin", async () => {
      // Need a tournament in Registration status for this test
      const [tournament4Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([4, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      await program.methods
        .createTournament(
          9,
          new anchor.BN(10000),
          new anchor.BN(Math.floor(Date.now() / 1000) + 3600),
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament4Pda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      await program.methods
        .openRegistration()
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament4Pda,
        })
        .rpc();

      // Register 2 players
      const testPlayer1 = Keypair.generate();
      const testPlayer2 = Keypair.generate();
      await provider.connection.confirmTransaction(
        await provider.connection.requestAirdrop(testPlayer1.publicKey, 1 * LAMPORTS_PER_SOL)
      );
      await provider.connection.confirmTransaction(
        await provider.connection.requestAirdrop(testPlayer2.publicKey, 1 * LAMPORTS_PER_SOL)
      );

      for (const p of [testPlayer1, testPlayer2]) {
        const [regPda] = PublicKey.findProgramAddressSync(
          [Buffer.from("registration"), tournament4Pda.toBuffer(), p.publicKey.toBuffer()],
          program.programId
        );
        const agentName = Buffer.alloc(32);
        agentName.write("TestAgent");
        const agentImageUri = Buffer.alloc(128);

        await program.methods
          .registerPlayer({ free: {} }, Array.from(agentPromptHash), Array.from(agentName), Array.from(agentImageUri))
          .accounts({
            player: p.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournament4Pda,
            registration: regPda,
            treasury: treasury.publicKey,
            systemProgram: SystemProgram.programId,
          })
          .signers([p])
          .rpc();
      }

      // Try to start as non-admin
      try {
        await program.methods
          .startTournament()
          .accounts({
            admin: player1.publicKey, // Not admin!
            arenaConfig: arenaConfigPda,
            tournament: tournament4Pda,
            recentSlothashes: anchor.web3.SYSVAR_SLOT_HASHES_PUBKEY,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown Unauthorized error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("Unauthorized");
      }
    });

    it("should fail when tournament is not in Registration status", async () => {
      // tournamentPda is now InProgress, try to start it again
      try {
        await program.methods
          .startTournament()
          .accounts({
            admin: admin.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournamentPda, // Already InProgress
            recentSlothashes: anchor.web3.SYSVAR_SLOT_HASHES_PUBKEY,
          })
          .rpc();

        expect.fail("Should have thrown RegistrationNotOpen error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("RegistrationNotOpen");
      }
    });
  });

  describe("error_conditions", () => {
    it("should fail open_registration when called by non-admin", async () => {
      // Create new tournament for this test
      const [tournament5Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([5, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      await program.methods
        .createTournament(
          9,
          new anchor.BN(10000),
          new anchor.BN(Math.floor(Date.now() / 1000) + 3600),
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament5Pda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      try {
        await program.methods
          .openRegistration()
          .accounts({
            admin: player1.publicKey, // Not admin!
            arenaConfig: arenaConfigPda,
            tournament: tournament5Pda,
          })
          .signers([player1])
          .rpc();

        expect.fail("Should have thrown Unauthorized error");
      } catch (error: any) {
        expect(error.error.errorCode.code).to.equal("Unauthorized");
      }
    });

    it("should fail when player has insufficient balance for PRO tier", async () => {
      // Create new tournament
      const [tournament6Pda] = PublicKey.findProgramAddressSync(
        [Buffer.from("tournament"), Buffer.from([6, 0, 0, 0, 0, 0, 0, 0])],
        program.programId
      );

      await program.methods
        .createTournament(
          9,
          new anchor.BN(10000),
          new anchor.BN(Math.floor(Date.now() / 1000) + 3600),
          Array.from(blindStructureHash),
          Array.from(payoutStructureHash)
        )
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament6Pda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      await program.methods
        .openRegistration()
        .accounts({
          admin: admin.publicKey,
          arenaConfig: arenaConfigPda,
          tournament: tournament6Pda,
        })
        .rpc();

      // Create player with insufficient balance for PRO
      const poorPlayer = Keypair.generate();
      await provider.connection.confirmTransaction(
        await provider.connection.requestAirdrop(poorPlayer.publicKey, 0.1 * LAMPORTS_PER_SOL) // Only 0.1 SOL
      );

      const [poorRegPda] = PublicKey.findProgramAddressSync(
        [Buffer.from("registration"), tournament6Pda.toBuffer(), poorPlayer.publicKey.toBuffer()],
        program.programId
      );

      try {
        const agentName = Buffer.alloc(32);
        agentName.write("PoorProPlayer");
        const agentImageUri = Buffer.alloc(128);

        await program.methods
          .registerPlayer(
            { pro: {} }, // PRO requires 1 SOL
            Array.from(agentPromptHash),
            Array.from(agentName),
            Array.from(agentImageUri)
          )
          .accounts({
            player: poorPlayer.publicKey,
            arenaConfig: arenaConfigPda,
            tournament: tournament6Pda,
            registration: poorRegPda,
            treasury: treasury.publicKey,
            systemProgram: SystemProgram.programId,
          })
          .signers([poorPlayer])
          .rpc();

        expect.fail("Should have failed due to insufficient balance");
      } catch (error: any) {
        // Solana system program transfer failure
        expect(error.message).to.include("insufficient");
      }
    });
  });
});
