import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PokerArena } from "../target/types/poker_arena";
import { Keypair, PublicKey, SystemProgram, LAMPORTS_PER_SOL, Transaction, sendAndConfirmTransaction } from "@solana/web3.js";
import { createHash } from "crypto";

/**
 * Devnet Verification Script
 * - Uses minimal SOL for testing
 * - Returns all SOL to developer wallet after tests
 */

const RENT_EXEMPT_MINIMUM = 0.002 * LAMPORTS_PER_SOL; // ~0.002 SOL for rent
const TEST_PLAYER_FUND = 0.01 * LAMPORTS_PER_SOL; // 0.01 SOL for test player (covers rent + fees)

async function main() {
  console.log("\n=== Poker Arena Devnet Verification ===\n");

  // Setup provider
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  const program = anchor.workspace.PokerArena as Program<PokerArena>;
  const connection = provider.connection;
  const adminWallet = provider.wallet;

  console.log("Program ID:", program.programId.toString());
  console.log("Admin Wallet:", adminWallet.publicKey.toString());

  const initialBalance = await connection.getBalance(adminWallet.publicKey);
  console.log("Initial Balance:", initialBalance / LAMPORTS_PER_SOL, "SOL\n");

  // Track accounts to close/refund
  const accountsToClose: { pubkey: PublicKey; lamports: number }[] = [];
  const testKeypairs: Keypair[] = [];

  // Test data
  const treasury = Keypair.generate();
  const pointsMint = Keypair.generate();
  const player1 = Keypair.generate();
  testKeypairs.push(player1);

  const blindStructureHash = createHash("sha256").update(JSON.stringify({ levels: [] })).digest();
  const payoutStructureHash = createHash("sha256").update(JSON.stringify({ payouts: [] })).digest();
  const agentPromptHash = createHash("sha256").update("test prompt").digest();

  // PDAs
  const [arenaConfigPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("arena_config")],
    program.programId
  );

  try {
    // ========== TEST 1: Initialize Arena Config ==========
    console.log("1. Testing Initialize...");

    // Check if already initialized
    let arenaConfig;
    try {
      arenaConfig = await program.account.arenaConfig.fetch(arenaConfigPda);
      console.log("   Arena already initialized, tournament count:", arenaConfig.tournamentCount.toNumber());
    } catch {
      // Initialize if not exists
      await program.methods
        .initialize(treasury.publicKey, pointsMint.publicKey)
        .accountsPartial({
          admin: adminWallet.publicKey,
          arenaConfig: arenaConfigPda,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      arenaConfig = await program.account.arenaConfig.fetch(arenaConfigPda);
      console.log("   Arena initialized successfully!");
    }
    console.log("   [PASS] Initialize\n");

    // ========== TEST 2: Create Tournament ==========
    console.log("2. Testing Create Tournament...");

    const tournamentId = arenaConfig.tournamentCount.toNumber() + 1;
    const tournamentIdBuffer = Buffer.alloc(8);
    tournamentIdBuffer.writeBigUInt64LE(BigInt(tournamentId));

    const [tournamentPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("tournament"), tournamentIdBuffer],
      program.programId
    );

    await program.methods
      .createTournament(
        9, // max_players (small for testing)
        new anchor.BN(10000), // starting_stack
        new anchor.BN(Math.floor(Date.now() / 1000) + 3600), // starts_at (1 hour from now)
        Array.from(blindStructureHash),
        Array.from(payoutStructureHash)
      )
      .accountsPartial({
        admin: adminWallet.publicKey,
        arenaConfig: arenaConfigPda,
        tournament: tournamentPda,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const tournament = await program.account.tournament.fetch(tournamentPda);
    console.log("   Tournament ID:", tournament.id.toNumber());
    console.log("   Max Players:", tournament.maxPlayers);
    console.log("   Status:", Object.keys(tournament.status)[0]);
    accountsToClose.push({ pubkey: tournamentPda, lamports: await connection.getBalance(tournamentPda) });
    console.log("   [PASS] Create Tournament on Devnet\n");

    // ========== TEST 3: Open Registration ==========
    console.log("3. Testing Open Registration...");

    await program.methods
      .openRegistration()
      .accountsPartial({
        admin: adminWallet.publicKey,
        arenaConfig: arenaConfigPda,
        tournament: tournamentPda,
      })
      .rpc();

    const tournamentAfterOpen = await program.account.tournament.fetch(tournamentPda);
    console.log("   Status:", Object.keys(tournamentAfterOpen.status)[0]);
    console.log("   [PASS] Open Registration\n");

    // ========== TEST 4: Register Player ==========
    console.log("4. Testing Register Player...");

    // Fund test player with minimal SOL (just enough for rent + transaction fee)
    const fundTx = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: adminWallet.publicKey,
        toPubkey: player1.publicKey,
        lamports: TEST_PLAYER_FUND,
      })
    );
    await provider.sendAndConfirm(fundTx);
    console.log("   Funded test player with", TEST_PLAYER_FUND / LAMPORTS_PER_SOL, "SOL");

    const [registrationPda] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("registration"),
        tournamentPda.toBuffer(),
        player1.publicKey.toBuffer(),
      ],
      program.programId
    );

    const agentName = Buffer.alloc(32);
    agentName.write("TestAgent");
    const agentImageUri = Buffer.alloc(128);
    agentImageUri.write("https://example.com/test.jpg");

    await program.methods
      .registerPlayer(
        { free: {} }, // FREE tier (no payment required)
        Array.from(agentPromptHash),
        Array.from(agentName),
        Array.from(agentImageUri)
      )
      .accountsPartial({
        player: player1.publicKey,
        arenaConfig: arenaConfigPda,
        tournament: tournamentPda,
        registration: registrationPda,
        treasury: treasury.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .signers([player1])
      .rpc();

    const registration = await program.account.playerRegistration.fetch(registrationPda);
    console.log("   Player registered:", registration.wallet.toString().slice(0, 8) + "...");
    console.log("   Tier:", Object.keys(registration.tier)[0]);
    accountsToClose.push({ pubkey: registrationPda, lamports: await connection.getBalance(registrationPda) });
    console.log("   [PASS] Register Player on Devnet\n");

    // ========== ALL TESTS PASSED ==========
    console.log("=== ALL VERIFICATION TESTS PASSED ===\n");

  } catch (error: any) {
    console.error("\n[FAIL] Test failed:", error.message);
    if (error.logs) {
      console.error("Logs:", error.logs);
    }
  } finally {
    // ========== CLEANUP: Return SOL to developer wallet ==========
    console.log("=== Cleanup: Returning SOL to developer wallet ===\n");

    // Return SOL from test player accounts
    for (const keypair of testKeypairs) {
      try {
        const balance = await connection.getBalance(keypair.publicKey);
        if (balance > 5000) { // Leave minimum for rent
          const returnAmount = balance - 5000; // Keep 5000 lamports for transaction fee
          const returnTx = new Transaction().add(
            SystemProgram.transfer({
              fromPubkey: keypair.publicKey,
              toPubkey: adminWallet.publicKey,
              lamports: returnAmount,
            })
          );
          await sendAndConfirmTransaction(connection, returnTx, [keypair]);
          console.log("   Returned", returnAmount / LAMPORTS_PER_SOL, "SOL from", keypair.publicKey.toString().slice(0, 8) + "...");
        }
      } catch (e: any) {
        console.log("   Could not return SOL from", keypair.publicKey.toString().slice(0, 8) + "...:", e.message);
      }
    }

    // Note: PDA accounts (tournament, registration) cannot be closed without program support
    // The rent SOL is locked in these accounts until a close instruction is added
    if (accountsToClose.length > 0) {
      const totalLocked = accountsToClose.reduce((sum, acc) => sum + acc.lamports, 0);
      console.log("\n   Note: ~" + (totalLocked / LAMPORTS_PER_SOL).toFixed(4) + " SOL locked in PDA accounts (requires close instruction to recover)");
    }

    const finalBalance = await connection.getBalance(adminWallet.publicKey);
    const netCost = (initialBalance - finalBalance) / LAMPORTS_PER_SOL;
    console.log("\n   Initial Balance:", initialBalance / LAMPORTS_PER_SOL, "SOL");
    console.log("   Final Balance:", finalBalance / LAMPORTS_PER_SOL, "SOL");
    console.log("   Net Cost:", netCost.toFixed(6), "SOL (mostly rent + tx fees)\n");
  }
}

main().catch(console.error);
