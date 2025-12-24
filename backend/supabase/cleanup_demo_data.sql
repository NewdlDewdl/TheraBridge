-- Demo Data Cleanup Function
-- Deletes demo users and their associated data older than 24 hours
-- Call this via cron job or manually

CREATE OR REPLACE FUNCTION cleanup_expired_demo_users()
RETURNS TABLE(deleted_users INT, deleted_sessions INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_deleted_users INT;
    v_deleted_sessions INT;
BEGIN
    -- Count sessions before deletion
    SELECT COUNT(*) INTO v_deleted_sessions
    FROM therapy_sessions ts
    INNER JOIN users u ON ts.patient_id = u.id
    WHERE u.is_demo = TRUE
      AND u.demo_expires_at < NOW();

    -- Delete sessions for expired demo users (CASCADE will handle related data)
    DELETE FROM therapy_sessions
    WHERE patient_id IN (
        SELECT id FROM users
        WHERE is_demo = TRUE
          AND demo_expires_at < NOW()
    );

    -- Delete expired demo users
    DELETE FROM users
    WHERE is_demo = TRUE
      AND demo_expires_at < NOW();

    GET DIAGNOSTICS v_deleted_users = ROW_COUNT;

    RETURN QUERY SELECT v_deleted_users, v_deleted_sessions;
END;
$$;

COMMENT ON FUNCTION cleanup_expired_demo_users() IS
'Deletes demo users and sessions expired beyond 24 hours. Returns count of deleted records.';

-- Example cron schedule (for Supabase pg_cron extension):
-- SELECT cron.schedule('cleanup-demo-users', '0 * * * *', 'SELECT cleanup_expired_demo_users()');
